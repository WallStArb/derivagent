-- Derivagent Database Schema for Supabase
-- Multi-tenant team-based architecture with Row-Level Security

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Custom types
CREATE TYPE team_type AS ENUM ('individual', 'small_firm', 'enterprise');
CREATE TYPE member_role AS ENUM ('owner', 'admin', 'trader', 'viewer');
CREATE TYPE broker_status AS ENUM ('connected', 'disconnected', 'error', 'pending');
CREATE TYPE position_status AS ENUM ('open', 'closed', 'expired');
CREATE TYPE order_status AS ENUM ('pending', 'filled', 'cancelled', 'rejected');

-- Teams table (multi-tenant organization)
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    type team_type NOT NULL DEFAULT 'individual',
    owner_id UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}',
    subscription_tier VARCHAR(20) DEFAULT 'free',
    CONSTRAINT teams_name_unique UNIQUE (name, owner_id)
);

-- Team members (many-to-many relationship)
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role member_role NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited_by UUID REFERENCES auth.users(id),
    CONSTRAINT team_members_unique UNIQUE (team_id, user_id)
);

-- User profiles (extended user data)
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    active_team_id UUID REFERENCES teams(id),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    company VARCHAR(100),
    phone VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Broker accounts (team-scoped)
CREATE TABLE broker_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    broker_name VARCHAR(50) NOT NULL, -- 'tastytrade', 'ibkr', 'schwab', etc.
    account_number VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    status broker_status DEFAULT 'pending',
    credentials_vault_path VARCHAR(200), -- HashiCorp Vault path
    api_settings JSONB DEFAULT '{}',
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    CONSTRAINT broker_accounts_unique UNIQUE (team_id, broker_name, account_number)
);

-- Trading strategies (team-scoped)
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'meic', 'iron_condor', 'strangle', etc.
    description TEXT,
    parameters JSONB NOT NULL DEFAULT '{}',
    risk_limits JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES auth.users(id)
);

-- Positions (team-scoped)
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    broker_account_id UUID NOT NULL REFERENCES broker_accounts(id),
    strategy_id UUID REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    underlying VARCHAR(10) NOT NULL,
    position_type VARCHAR(20) NOT NULL, -- 'long_call', 'short_put', etc.
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10, 4),
    current_price DECIMAL(10, 4),
    unrealized_pnl DECIMAL(12, 4),
    realized_pnl DECIMAL(12, 4),
    status position_status DEFAULT 'open',
    expiration DATE,
    strike_price DECIMAL(10, 4),
    option_type VARCHAR(10), -- 'call', 'put', null for stock
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Orders (team-scoped)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    broker_account_id UUID NOT NULL REFERENCES broker_accounts(id),
    strategy_id UUID REFERENCES strategies(id),
    broker_order_id VARCHAR(100),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'buy', 'sell'
    quantity INTEGER NOT NULL,
    order_type VARCHAR(20) NOT NULL, -- 'market', 'limit', 'stop'
    limit_price DECIMAL(10, 4),
    stop_price DECIMAL(10, 4),
    status order_status DEFAULT 'pending',
    filled_quantity INTEGER DEFAULT 0,
    avg_fill_price DECIMAL(10, 4),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    filled_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    ai_reasoning TEXT, -- AI explanation for the order
    human_approved BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'
);

-- AI agent sessions (team-scoped)
CREATE TABLE ai_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL, -- 'market_regime', 'volatility_surface', etc.
    session_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES auth.users(id)
);

-- AI agent responses (for caching and audit)
CREATE TABLE ai_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    model_used VARCHAR(50) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL, -- SHA-256 of prompt for caching
    request_data JSONB NOT NULL,
    response_data JSONB NOT NULL,
    usage_stats JSONB DEFAULT '{}', -- token counts, cost, etc.
    processing_time_ms INTEGER,
    cache_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Market data cache (shared across teams)
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(30) NOT NULL, -- 'quote', 'option_chain', 'greeks'
    data JSONB NOT NULL,
    source VARCHAR(30) NOT NULL, -- 'polygon', 'alpha_vantage', etc.
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT market_data_unique UNIQUE (symbol, data_type, source, timestamp)
);

-- Audit log (team-scoped)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(30) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_teams_owner ON teams(owner_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);
CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_user_profiles_active_team ON user_profiles(active_team_id);
CREATE INDEX idx_broker_accounts_team ON broker_accounts(team_id);
CREATE INDEX idx_positions_team_status ON positions(team_id, status);
CREATE INDEX idx_orders_team_status ON orders(team_id, status);
CREATE INDEX idx_ai_responses_hash ON ai_responses(prompt_hash);
CREATE INDEX idx_ai_responses_cache ON ai_responses(cache_until);
CREATE INDEX idx_market_data_symbol_type ON market_data(symbol, data_type);
CREATE INDEX idx_market_data_expires ON market_data(expires_at);
CREATE INDEX idx_audit_log_team_action ON audit_log(team_id, action);

-- Row-Level Security Policies
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE broker_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Helper function to get user's team context
CREATE OR REPLACE FUNCTION get_user_team_context()
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_id UUID;
    team_id UUID;
BEGIN
    -- Get current user ID
    user_id := auth.uid();
    IF user_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Get active team from user profile or first team membership
    SELECT active_team_id INTO team_id
    FROM user_profiles 
    WHERE user_profiles.user_id = get_user_team_context.user_id;
    
    -- If no active team set, get first team membership
    IF team_id IS NULL THEN
        SELECT tm.team_id INTO team_id
        FROM team_members tm
        WHERE tm.user_id = get_user_team_context.user_id
        ORDER BY tm.joined_at
        LIMIT 1;
    END IF;
    
    RETURN team_id;
END;
$$;

-- Function to set active team context
CREATE OR REPLACE FUNCTION set_active_team_context(team_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_id UUID;
    is_member BOOLEAN;
BEGIN
    user_id := auth.uid();
    IF user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user is member of team
    SELECT EXISTS(
        SELECT 1 FROM team_members 
        WHERE team_members.user_id = set_active_team_context.user_id 
        AND team_members.team_id = set_active_team_context.team_id
    ) INTO is_member;
    
    IF NOT is_member THEN
        RETURN FALSE;
    END IF;
    
    -- Update user's active team
    INSERT INTO user_profiles (user_id, active_team_id, updated_at)
    VALUES (set_active_team_context.user_id, set_active_team_context.team_id, NOW())
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        active_team_id = set_active_team_context.team_id,
        updated_at = NOW();
    
    RETURN TRUE;
END;
$$;

-- RLS Policies for teams
CREATE POLICY "Users can view teams they belong to" ON teams
    FOR SELECT USING (
        id IN (
            SELECT team_id FROM team_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Team owners can update their teams" ON teams
    FOR UPDATE USING (owner_id = auth.uid());

-- RLS Policies for team_members
CREATE POLICY "Users can view team memberships they belong to" ON team_members
    FOR SELECT USING (
        team_id IN (
            SELECT team_id FROM team_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Team admins can manage members" ON team_members
    FOR ALL USING (
        team_id IN (
            SELECT tm.team_id FROM team_members tm
            WHERE tm.user_id = auth.uid() 
            AND tm.role IN ('owner', 'admin')
        )
    );

-- RLS Policies for user_profiles
CREATE POLICY "Users can manage their own profile" ON user_profiles
    FOR ALL USING (user_id = auth.uid());

-- RLS Policies for team-scoped tables
CREATE POLICY "Team members can access broker accounts" ON broker_accounts
    FOR SELECT USING (team_id = get_user_team_context());

CREATE POLICY "Team admins can manage broker accounts" ON broker_accounts
    FOR ALL USING (
        team_id IN (
            SELECT tm.team_id FROM team_members tm
            WHERE tm.user_id = auth.uid() 
            AND tm.role IN ('owner', 'admin')
        )
    );

CREATE POLICY "Team members can access positions" ON positions
    FOR SELECT USING (team_id = get_user_team_context());

CREATE POLICY "Team traders can manage positions" ON positions
    FOR ALL USING (
        team_id IN (
            SELECT tm.team_id FROM team_members tm
            WHERE tm.user_id = auth.uid() 
            AND tm.role IN ('owner', 'admin', 'trader')
        )
    );

CREATE POLICY "Team members can access orders" ON orders
    FOR SELECT USING (team_id = get_user_team_context());

CREATE POLICY "Team traders can manage orders" ON orders
    FOR ALL USING (
        team_id IN (
            SELECT tm.team_id FROM team_members tm
            WHERE tm.user_id = auth.uid() 
            AND tm.role IN ('owner', 'admin', 'trader')
        )
    );

CREATE POLICY "Team members can access strategies" ON strategies
    FOR SELECT USING (team_id = get_user_team_context());

CREATE POLICY "Team traders can manage strategies" ON strategies
    FOR ALL USING (
        team_id IN (
            SELECT tm.team_id FROM team_members tm
            WHERE tm.user_id = auth.uid() 
            AND tm.role IN ('owner', 'admin', 'trader')
        )
    );

CREATE POLICY "Team members can access AI sessions" ON ai_sessions
    FOR ALL USING (team_id = get_user_team_context());

CREATE POLICY "Team members can access AI responses" ON ai_responses
    FOR ALL USING (team_id = get_user_team_context());

CREATE POLICY "Team members can access audit log" ON audit_log
    FOR SELECT USING (team_id = get_user_team_context());

-- Market data is shared (no RLS)
-- Everyone can read market data for performance

-- Functions for automatic timestamping
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_teams_updated_at 
    BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_broker_accounts_updated_at 
    BEFORE UPDATE ON broker_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at 
    BEFORE UPDATE ON strategies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Automatic audit logging function
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        team_id,
        user_id,
        action,
        resource_type,
        resource_id,
        details
    ) VALUES (
        COALESCE(NEW.team_id, OLD.team_id),
        auth.uid(),
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        CASE 
            WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD)
            ELSE to_jsonb(NEW)
        END
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to sensitive tables
CREATE TRIGGER audit_orders AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_positions AFTER INSERT OR UPDATE OR DELETE ON positions
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_broker_accounts AFTER INSERT OR UPDATE OR DELETE ON broker_accounts
    FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- Cleanup functions for data retention
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up expired market data
    DELETE FROM market_data WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old AI responses (older than 30 days)
    DELETE FROM ai_responses 
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND cache_until < NOW();
    
    -- Clean up old audit logs (older than 1 year)
    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '1 year';
    
    RETURN deleted_count;
END;
$$;

-- Schedule cleanup job (requires pg_cron extension)
SELECT cron.schedule('cleanup-expired-data', '0 2 * * *', 'SELECT cleanup_expired_data();');
-- Database Initialization Script for XCreator Pro + Eliza Integration
-- This script sets up the unified database schema

-- Create database if not exists (for development environments)
-- CREATE DATABASE IF NOT EXISTS xcreator_eliza;
-- USE xcreator_eliza;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(100),
    website TEXT,
    is_verified BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notifications JSONB DEFAULT '{}',
    privacy JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unified characters table
CREATE TABLE IF NOT EXISTS characters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    display_name VARCHAR(100),
    eliza_agent_id VARCHAR(100) UNIQUE,
    personality JSONB NOT NULL,
    voice JSONB,
    avatar JSONB,
    settings JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    visibility VARCHAR(20) DEFAULT 'public',
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create character statistics table
CREATE TABLE IF NOT EXISTS character_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    total_interactions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    average_response_time INTEGER DEFAULT 0,
    engagement_score DECIMAL(3,2) DEFAULT 0,
    satisfaction_score DECIMAL(3,2) DEFAULT 0,
    last_interaction TIMESTAMP WITH TIME ZONE,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(character_id, date)
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    session_id UUID DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    response_time INTEGER,
    context JSONB DEFAULT '{}',
    platform VARCHAR(50) DEFAULT 'xcreator-pro',
    sentiment_score DECIMAL(3,2),
    engagement_score DECIMAL(3,2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create conversation sessions table
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Create generated content table
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'generated',
    platform VARCHAR(50),
    scheduled_for TIMESTAMP WITH TIME ZONE,
    posted_at TIMESTAMP WITH TIME ZONE,
    engagement_stats JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create social media accounts table
CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    account_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create social media engagement table
CREATE TABLE IF NOT EXISTS social_engagement (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    social_account_id UUID REFERENCES social_accounts(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_content_id VARCHAR(100),
    target_user_id VARCHAR(100),
    target_username VARCHAR(100),
    engagement_data JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create autonomous operations table
CREATE TABLE IF NOT EXISTS autonomous_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL,
    operation_data JSONB NOT NULL,
    trigger_type VARCHAR(50),
    trigger_data JSONB DEFAULT '{}',
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    execution_time INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create performance analytics table
CREATE TABLE IF NOT EXISTS performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(character_id, metric_type, date)
);

-- Create API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    tier VARCHAR(20) DEFAULT 'free',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create API usage table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time INTEGER,
    user_agent TEXT,
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create affiliate links table
CREATE TABLE IF NOT EXISTS affiliate_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    affiliate VARCHAR(100) NOT NULL,
    product_id VARCHAR(100),
    tracking_id VARCHAR(100) UNIQUE NOT NULL,
    link TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    commission DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create affiliate conversions table
CREATE TABLE IF NOT EXISTS affiliate_conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    affiliate_link_id UUID REFERENCES affiliate_links(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    commission DECIMAL(10,2) NOT NULL,
    conversion_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    start_date DATE NOT NULL,
    end_date DATE,
    auto_renew BOOLEAN DEFAULT true,
    payment_method VARCHAR(50),
    payment_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create usage tracking table
CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    character_id UUID REFERENCES characters(id) ON DELETE CASCADE,
    tool VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    amount INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    date DATE DEFAULT CURRENT_DATE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create files table for uploads
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size INTEGER NOT NULL,
    path TEXT NOT NULL,
    url TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_status ON characters(status);
CREATE INDEX IF NOT EXISTS idx_conversations_character_id ON conversations(character_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_generated_content_character_id ON generated_content(character_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_status ON generated_content(status);
CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_links_user_id ON affiliate_links(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_id ON usage_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_date ON usage_tracking(date);

-- Create functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_characters_updated_at ON characters;
CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (for development)
INSERT INTO users (email, username, password_hash, display_name, is_verified, is_active)
VALUES (
    'admin@xcreator-pro.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewqNNgL3GJ6xXxPa', -- password: admin123
    'Platform Admin',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Insert default character (for testing)
INSERT INTO characters (user_id, name, display_name, personality, settings)
VALUES (
    (SELECT id FROM users WHERE email = 'admin@xcreator-pro.com'),
    'AI Assistant',
    'XCreator Pro Assistant',
    '{
        "traits": ["helpful", "knowledgeable", "friendly"],
        "communication_style": "professional",
        "background": "AI assistant for XCreator Pro platform",
        "interests": ["technology", "content creation", "AI"],
        "tone": "professional yet approachable"
    }'::jsonb,
    '{
        "visibility": "public",
        "auto_response": true,
        "content_generation": true
    }'::jsonb
) ON CONFLICT DO NOTHING;

-- Create views for analytics
CREATE OR REPLACE VIEW character_analytics_summary AS
SELECT 
    c.id as character_id,
    c.name,
    c.status,
    COALESCE(SUM(cs.total_interactions), 0) as total_interactions,
    COALESCE(SUM(cs.total_messages), 0) as total_messages,
    COALESCE(AVG(cs.average_response_time), 0) as avg_response_time,
    COALESCE(AVG(cs.engagement_score), 0) as avg_engagement_score,
    MAX(cs.last_interaction) as last_interaction,
    COUNT(DISTINCT conv.id) as total_conversations,
    COUNT(DISTINCT gc.id) as total_content_generated
FROM characters c
LEFT JOIN character_stats cs ON c.id = cs.character_id
LEFT JOIN conversations conv ON c.id = conv.character_id
LEFT JOIN generated_content gc ON c.id = gc.character_id
WHERE c.status = 'active'
GROUP BY c.id, c.name, c.status;

CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT 
    date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(DISTINCT character_id) as active_characters,
    SUM(amount) as total_usage,
    COUNT(*) as total_actions
FROM usage_tracking
GROUP BY date
ORDER BY date DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Log completion
SELECT 'Database initialization completed successfully' as status;
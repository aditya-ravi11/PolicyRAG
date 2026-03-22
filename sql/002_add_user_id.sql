-- Add user_id column to documents table
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);
UPDATE documents SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
ALTER TABLE documents ALTER COLUMN user_id SET NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- Add user_id column to evaluation_history table
ALTER TABLE evaluation_history ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);
UPDATE evaluation_history SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
ALTER TABLE evaluation_history ALTER COLUMN user_id SET NOT NULL;

-- Row Level Security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_documents_select" ON documents FOR SELECT USING (auth.uid()::text = user_id);
CREATE POLICY "users_own_documents_insert" ON documents FOR INSERT WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "users_own_documents_delete" ON documents FOR DELETE USING (auth.uid()::text = user_id);

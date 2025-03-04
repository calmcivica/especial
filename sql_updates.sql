-- SQL script for database schema updates to support gamification and improved concurrency

-- Add columns to support gamification in the Specializations database
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('[esnowflake].[dbo].Dim_Users') AND name = 'xp')
BEGIN
    ALTER TABLE [esnowflake].[dbo].Dim_Users
    ADD xp INT DEFAULT 0,
        level INT DEFAULT 1,
        streak_days INT DEFAULT 0,
        last_active DATETIME DEFAULT GETDATE()
END

-- Add columns to support gamification in the SQL database
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('[dbo].Dim_Users') AND name = 'xp')
BEGIN
    ALTER TABLE [dbo].Dim_Users
    ADD xp INT DEFAULT 0,
        level INT DEFAULT 1,
        streak_days INT DEFAULT 0,
        last_active DATETIME DEFAULT GETDATE()
END

-- Create XP history table for Specializations
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Fact_XP_History' AND schema_id = SCHEMA_ID('dbo') AND OBJECT_ID LIKE '%[esnowflake]%')
BEGIN
    CREATE TABLE [esnowflake].[dbo].Fact_XP_History
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_nickname NVARCHAR(255) NOT NULL,
        xp_amount INT NOT NULL,
        reason NVARCHAR(255) NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (user_nickname) REFERENCES [esnowflake].[dbo].Dim_Users(name)
    )
    CREATE INDEX IX_XP_History_User ON [esnowflake].[dbo].Fact_XP_History(user_nickname)
END

-- Create XP history table for SQL
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Fact_XP_History' AND schema_id = SCHEMA_ID('dbo') AND OBJECT_ID NOT LIKE '%[esnowflake]%')
BEGIN
    CREATE TABLE [dbo].Fact_XP_History
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(255) NOT NULL,
        xp_amount INT NOT NULL,
        reason NVARCHAR(255) NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (username) REFERENCES [dbo].Dim_Users(username)
    )
    CREATE INDEX IX_XP_History_User ON [dbo].Fact_XP_History(username)
END

-- Create achievement table for Specializations
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Dim_Achievements' AND schema_id = SCHEMA_ID('dbo') AND OBJECT_ID LIKE '%[esnowflake]%')
BEGIN
    CREATE TABLE [esnowflake].[dbo].Dim_Achievements
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        description NVARCHAR(500) NOT NULL,
        xp_reward INT NOT NULL DEFAULT 0,
        icon NVARCHAR(50) NULL
    )
    
    -- Create user achievements table
    CREATE TABLE [esnowflake].[dbo].Fact_User_Achievements
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_nickname NVARCHAR(255) NOT NULL,
        achievement_id INT NOT NULL,
        earned_date DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (user_nickname) REFERENCES [esnowflake].[dbo].Dim_Users(name),
        FOREIGN KEY (achievement_id) REFERENCES [esnowflake].[dbo].Dim_Achievements(id),
        CONSTRAINT UQ_User_Achievement UNIQUE (user_nickname, achievement_id)
    )
    
    -- Insert default achievements
    INSERT INTO [esnowflake].[dbo].Dim_Achievements (name, description, xp_reward, icon)
    VALUES 
        ('First Steps', 'Answer your first question correctly', 10, '🏆'),
        ('Perfect Exam', 'Complete an exam with 100% correct answers', 50, '🥇'),
        ('3-Day Streak', 'Study for 3 consecutive days', 15, '🔥'),
        ('7-Day Streak', 'Study for 7 consecutive days', 30, '🔥🔥'),
        ('30-Day Streak', 'Study for 30 consecutive days', 100, '🔥🔥🔥'),
        ('Knowledge Seeker', 'Answer 50 questions', 25, '📚'),
        ('Knowledge Master', 'Answer 200 questions', 75, '📚📚')
END

-- Create achievement table for SQL
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Dim_Achievements' AND schema_id = SCHEMA_ID('dbo') AND OBJECT_ID NOT LIKE '%[esnowflake]%')
BEGIN
    CREATE TABLE [dbo].Dim_Achievements
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        description NVARCHAR(500) NOT NULL,
        xp_reward INT NOT NULL DEFAULT 0,
        icon NVARCHAR(50) NULL
    )
    
    -- Create user achievements table
    CREATE TABLE [dbo].Fact_User_Achievements
    (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(255) NOT NULL,
        achievement_id INT NOT NULL,
        earned_date DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (username) REFERENCES [dbo].Dim_Users(username),
        FOREIGN KEY (achievement_id) REFERENCES [dbo].Dim_Achievements(id),
        CONSTRAINT UQ_SQL_User_Achievement UNIQUE (username, achievement_id)
    )
    
    -- Insert default achievements
    INSERT INTO [dbo].Dim_Achievements (name, description, xp_reward, icon)
    VALUES 
        ('SQL First Steps', 'Answer your first SQL question correctly', 10, '🏆'),
        ('SQL Wizard', 'Complete 5 SQL exercises correctly', 50, '🧙'),
        ('3-Day Streak', 'Practice SQL for 3 consecutive days', 15, '🔥'),
        ('7-Day Streak', 'Practice SQL for 7 consecutive days', 30, '🔥🔥'),
        ('30-Day Streak', 'Practice SQL for 30 consecutive days', 100, '🔥🔥🔥'),
        ('Query Master', 'Complete 20 SQL exercises', 75, '💻')
END

-- Update indexes for better concurrent performance
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FACT_ANSWERS_USER' AND object_id = OBJECT_ID('[esnowflake].[dbo].FACT_ANSWERS'))
BEGIN
    CREATE INDEX IX_FACT_ANSWERS_USER ON [esnowflake].[dbo].FACT_ANSWERS (user_nickname, question_id)
END

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FACT_ANSWERS_SQL_USER' AND object_id = OBJECT_ID('[dbo].Fact_Answers'))
BEGIN
    CREATE INDEX IX_FACT_ANSWERS_SQL_USER ON [dbo].Fact_Answers (username, question_id)
END

-- Update stored procedures for better concurrency
IF OBJECT_ID('[esnowflake].[dbo].sp_RecordAnswer', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE [esnowflake].[dbo].sp_RecordAnswer
END

GO

CREATE PROCEDURE [esnowflake].[dbo].sp_RecordAnswer
    @question_id INT,
    @user_nickname NVARCHAR(255),
    @type NVARCHAR(50),
    @exam_id INT = NULL,
    @is_correct BIT,
    @is_answered BIT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Insert answer record with retry logic
        DECLARE @retry INT = 0;
        DECLARE @success BIT = 0;
        DECLARE @error NVARCHAR(MAX);
        
        WHILE @retry < 3 AND @success = 0
        BEGIN
            BEGIN TRY
                INSERT INTO [esnowflake].[dbo].Fact_Answers 
                    (question_id, user_nickname, type, exam_id, is_correct, is_answered, ANSWER_TIMESTAMP)
                VALUES 
                    (@question_id, @user_nickname, @type, @exam_id, @is_correct, @is_answered, CURRENT_TIMESTAMP);
                
                SET @success = 1;
            END TRY
            BEGIN CATCH
                SET @error = ERROR_MESSAGE();
                SET @retry = @retry + 1;
                WAITFOR DELAY '00:00:00.1'; -- Wait 100ms before retry
            END CATCH
        END
        
        IF @success = 0
        BEGIN
            THROW 50000, @error, 1;
        END
        
        -- Award XP for correct answers (only in practice mode)
        IF @is_correct = 1 AND @type = 'practicar'
        BEGIN
            -- Add 5 XP for correct answers
            UPDATE [esnowflake].[dbo].Dim_Users
            SET xp = ISNULL(xp, 0) + 5,
                last_active = CURRENT_TIMESTAMP
            WHERE name = @user_nickname;
            
            -- Record XP gain
            INSERT INTO [esnowflake].[dbo].Fact_XP_History 
                (user_nickname, xp_amount, reason, timestamp)
            VALUES
                (@user_nickname, 5, 'Correct answer', CURRENT_TIMESTAMP);
        END
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        THROW;
    END CATCH
END

GO

-- Create stored procedure for SQL answers with XP
IF OBJECT_ID('[dbo].sp_RecordSQLAnswer', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE [dbo].sp_RecordSQLAnswer
END

GO

CREATE PROCEDURE [dbo].sp_RecordSQLAnswer
    @question_id INT,
    @username NVARCHAR(255),
    @is_correct BIT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Insert answer record with retry logic
        DECLARE @retry INT = 0;
        DECLARE @success BIT = 0;
        DECLARE @error NVARCHAR(MAX);
        
        WHILE @retry < 3 AND @success = 0
        BEGIN
            BEGIN TRY
                INSERT INTO [dbo].Fact_Answers 
                    (question_id, username, is_correct, timestamp)
                VALUES 
                    (@question_id, @username, @is_correct, CURRENT_TIMESTAMP);
                
                SET @success = 1;
            END TRY
            BEGIN CATCH
                SET @error = ERROR_MESSAGE();
                SET @retry = @retry + 1;
                WAITFOR DELAY '00:00:00.1'; -- Wait 100ms before retry
            END CATCH
        END
        
        IF @success = 0
        BEGIN
            THROW 50000, @error, 1;
        END
        
        -- Award XP for correct answers
        IF @is_correct = 1
        BEGIN
            -- Add 10 XP for correct SQL answers (harder than regular questions)
            UPDATE [dbo].Dim_Users
            SET xp = ISNULL(xp, 0) + 10,
                last_active = CURRENT_TIMESTAMP
            WHERE username = @username;
            
            -- Record XP gain
            INSERT INTO [dbo].Fact_XP_History 
                (username, xp_amount, reason, timestamp)
            VALUES
                (@username, 10, 'Correct SQL query', CURRENT_TIMESTAMP);
        END
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        THROW;
    END CATCH
END
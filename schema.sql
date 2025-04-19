-- Create views for SQLite - note that SQLite syntax is different
-- View for User Activity Summary
CREATE VIEW IF NOT EXISTS user_activity_summary AS
SELECT 
    u.username,
    COUNT(DISTINCT r.id) AS total_requests,
    COUNT(DISTINCT d.id) AS total_downloads,
    COUNT(DISTINCT n.id) AS total_notifications,
    MAX(u.last_activity) AS last_activity
FROM users u
LEFT JOIN requests r ON u.id = r.user_id
LEFT JOIN downloads d ON r.id = d.request_id
LEFT JOIN notifications n ON u.id = n.user_id
GROUP BY u.username;

-- View for Download Progress
CREATE VIEW IF NOT EXISTS download_progress AS
SELECT 
    d.id AS download_id,
    r.title AS media_title,
    d.torrent_name,
    d.download_status,
    d.progress,
    d.estimated_completion_time
FROM downloads d
JOIN requests r ON d.request_id = r.id;

-- View for Recent Recommendations
CREATE VIEW IF NOT EXISTS recent_recommendations AS
SELECT 
    r.media_title,
    r.related_media_title,
    r.sent_to_email,
    r.recommendation_date,
    r.confidence_score,
    r.rating
FROM recommendations r
WHERE r.sent_status = 1;  -- SQLite uses 1/0 instead of TRUE/FALSE

-- Create triggers for SQLite - syntax differs from MySQL
-- Trigger for Inserting Audit Logs on User Actions
CREATE TRIGGER IF NOT EXISTS after_request_insert
AFTER INSERT ON requests
BEGIN
    INSERT INTO audit_logs (
        user_id, action_type, action_details, table_affected, action_timestamp
    ) VALUES (
        NEW.user_id,
        'INSERT',
        'New request created: ' || NEW.title,
        'requests',
        datetime('now')
    );
END;

-- Sample data insertion for requests table
-- Note: In SQLite, use single quotes for strings and datetime('now') for current timestamp
INSERT INTO requests (user_id, media_type, title, status, priority, requested_at)
VALUES
    (2, 'Movie', 'Justice League', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'Jungle Cruise', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'King Arthur: Legend of the Sword', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'Kingsman: The Secret Service', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'Kingsman: The Golden Circle', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'Kong: Skull Island', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'Legend', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'The Lord of the Rings: The Two Towers', 'Pending', 'Medium', datetime('now')),
    (2, 'Movie', 'The Lord of the Rings: The Fellowship of the Ring', 'Pending', 'Medium', datetime('now')),
    (2, 'TV Show', 'SEAL Team', 'Pending', 'Medium', datetime('now'));

-- Trigger for Updating Last Activity Timestamp
CREATE TRIGGER IF NOT EXISTS update_last_activity
AFTER INSERT ON requests
BEGIN
    UPDATE users
    SET last_activity = datetime('now')
    WHERE id = NEW.user_id;
END;

-- Trigger for Notification Sent Logging
CREATE TRIGGER IF NOT EXISTS after_notification_sent
AFTER INSERT ON notifications
BEGIN
    INSERT INTO audit_logs (
        user_id, action_type, action_details, table_affected, action_timestamp
    ) VALUES (
        NEW.user_id,
        'NOTIFICATION',
        'Notification sent: ' || NEW.message,
        'notifications',
        datetime('now')
    );
END;

-- Trigger for Marking Recommendations as Sent
CREATE TRIGGER IF NOT EXISTS mark_recommendation_sent
AFTER INSERT ON notifications
WHEN NEW.notification_type = 'Recommendation'
BEGIN
    UPDATE recommendations
    SET sent_status = 1
    WHERE id = NEW.reference_id;
END;
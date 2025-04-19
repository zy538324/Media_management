-- Stored Procedure for Archiving Old Recommendations
DELIMITER //

-- View for User Activity Summary
CREATE VIEW user_activity_summary AS
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
CREATE VIEW download_progress AS
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
CREATE VIEW recent_recommendations AS
SELECT 
    r.media_title,
    r.related_media_title,
    r.sent_to_email,
    r.recommendation_date,
    r.confidence_score,
    r.rating
FROM recommendations r
WHERE r.sent_status = TRUE;

-- Trigger for Inserting Audit Logs on User Actions
CREATE TRIGGER after_request_insert
AFTER INSERT ON requests
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (
        user_id, action_type, action_details, table_affected, action_timestamp
    ) VALUES (
        NEW.user_id,
        'Request Creation',
        CONCAT('Request for media: ', NEW.title),
        'requests',
        NOW()
    );
END//

INSERT INTO `requests` (`user_id`, `media_type`, `title`, `status`, `priority`, `requested_at`, `last_status_update`)
VALUES
    (2, 'Movie', 'Justice League', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Jungle Cruise', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'King Arthur: Legend of the Sword', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Kingsman: The Secret Service', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Kingsman: The Golden Circle', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Kong: Skull Island', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Legend', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Lord of the Rings: The Two Towers', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Lord of the Rings: The Fellowship of the Ring', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Layer Cake', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Lord of the Rings: The Return of the King', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Logan', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Longlegs', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Last Duel', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Master and Commander: The Far Side of the World', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Marvels', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Mission: Impossible - Dead Reckoning Part One', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Man of Steel', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Mission: Impossible III', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Moana 2', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Man from U.N.C.L.E.', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Matrix Resurrections', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Mummy Returns', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Matrix', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Matrix Reloaded', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Mummy', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Mission: Impossible - Fallout', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Mission: Impossible - Ghost Protocol', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Mission: Impossible - Rogue Nation', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'National Treasure: Book of Secrets', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'No Time to Die', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Napoleon', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Oppenheimer', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Paddington in Peru', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pirates of the Caribbean: At World\'s End', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pirates of the Caribbean: Dead Man\'s Chest', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pirates of the Caribbean: The Curse of the Black Pearl', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pirates of the Caribbean: On Stranger Tides', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pirates of the Caribbean: Dead Men Tell No Tales', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Pacific Rim', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Quantum of Solace', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Rogue One: A Star Wars Story', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Return of the Jedi', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Solo: A Star Wars Story', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Snatch', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: Episode III - Revenge of the Sith', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Spider-Man: No Way Home', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: The Last Jedi', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Spider-Man: Far From Home', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Shang-Chi and the Legend of the Ten Rings', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Shazam! Fury of the Gods', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Skyfall', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: Episode I - The Phantom Menace', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Spider-Man: Homecoming', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: Episode II - Attack of the Clones', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Empire Strikes Back', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: The Rise of Skywalker', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Star Wars: The Force Awakens', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Spectre', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Suicide Squad', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Thor: Ragnarok', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Thor: Love and Thunder', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Thor', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Tinker Tailor Soldier Spy', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Thor: The Dark World', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Venom: The Last Dance', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'The Wolverine', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Wonder Woman 1984', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Wonder Woman', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Wicked', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X2', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X-Men: Apocalypse', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X-Men: First Class 35mm Special', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X-Men: Days of Future Past', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X-Men Origins: Wolverine', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'X-Men: The Last Stand', 'Pending', 'Medium', NOW(), NULL),
    (2, 'Movie', 'Zack Snyder\'s Justice League', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Britain\'s Bloodiest Dynasty', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Poldark', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Inside the Tower of London', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'For All Mankind', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', '9-1-1: Lone Star', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', '1883', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', '1923', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Justified: City Primeval', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Landman', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Mayor of Kingstown', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Miss Scarlet and the Duke', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Tokyo Vice', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Ted Lasso', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'A Thousand Blows', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Walker', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Warrior', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Downton Abbey', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Digging for Britain', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'KAOS', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Outlander', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'The Gilded Age', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Yellowstone', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Blitz: The Bombs That Changed Britain', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Bergerac', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Britain\'s Most Historic Towns', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Bridgerton', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Robson Green\'s Weekend Escapes', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Reacher', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Ripper Street', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'The Rookie', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Slow Horses', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'Steeltown Murders', 'Pending', 'Medium', NOW(), NULL),
    (2, 'TV Show', 'SEAL Team', 'Pending', 'Medium', NOW(), NULL);

-- Trigger for Updating Last Activity Timestamp
CREATE TRIGGER update_last_activity
AFTER INSERT OR UPDATE ON requests
FOR EACH ROW
BEGIN
    UPDATE users
      SET last_activity = NOW()
    WHERE id = NEW.user_id;
END//

-- Trigger for Notification Sent Logging
CREATE TRIGGER after_notification_sent
AFTER INSERT ON notifications
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (
        user_id, action_type, action_details, table_affected, action_timestamp
    ) VALUES (
        NEW.user_id,
        'Notification Sent',
        CONCAT('Notification sent: ', NEW.content),
        'notifications',
        NOW()
    );
END//

-- Trigger for Marking Recommendations as Sent
CREATE TRIGGER mark_recommendation_sent
AFTER INSERT ON notifications
FOR EACH ROW
BEGIN
    IF NEW.notification_type = 'Recommendation' THEN
        UPDATE recommendations
           SET sent_status = TRUE
         WHERE sent_to_email = NEW.user_id;
    END IF;
END//

DELIMITER ;
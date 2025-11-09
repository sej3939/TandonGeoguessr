-- USER LOGIN:

SELECT player_id, username
FROM player
WHERE email = /* email inputted */ AND password = /* password inputted */;

-- If a row is returned, the user has sucessfully logged in. 
-- If no row is returned, the user entered an invalid email-password combination.

-- USER SIGNUP: 

INSERT INTO player (username, email, password)
VALUES (/* inputted username, email, password */)

-- Populates player table with new player account information.
-- In future implementation, passwords will be hashed before stored. 

-- POPULATING CUSTOM GAMES LIST: 

SELECT c.custom_game_id, p.username AS creator
FROM custom_game c
INNER JOIN player p ON c.player_id = p.player_id;

-- Returns all custom games with their associated creator.
-- This will populate the table in the custom game search screen.

-- SEARCHING CUSTOM GAMES LIST BY GAME ID OR CREATOR NAME:

SELECT c.custom_game_id, p.username AS creator
FROM custom_game c
INNER JOIN player p ON c.player_id = p.player_id
WHERE p.username LIKE /* input search term */ 
   OR c.custom_game_name LIKE /* input search term */;

-- Returns any custom games that match the search term inputted. 
-- Used for the search feature in the custom game search screen.

-- START NORMAL GAME SESSION: 

INSERT INTO game_session (player_id, total_score)
VALUES (/* inputted player id */, 0);

-- Creates new game session for player id with the score initialized to 0.

-- START CUSTOM GAME SESSION: 

INSERT INTO custom_game_session (player_id, custom_game_id, total_score)
VALUES (/* inputted player id , selected custom game id */, 0);

-- START CUSTOM GAME: 

INSERT INTO custom_game (player_id, custom_game_name)
VALUES (/* inputted player_id , custom game name */);

-- FETCH PHOTO FOR GUESS: 

SELECT photo_id, photo_data, room, floor, building
FROM photo
ORDER BY RAND()
LIMIT 1;

-- Randomly select photo from the database along with its room, floor, and building.
-- Used to display image on guessing page as well as keeping track of its correct room, floor and building.

-- ADDING PHOTOS TO CUSTOM GAME:

INSERT INTO custom_photo_pool (custom_game_id, photo_id)
VALUES (/* custom game id , selected photo id */);

-- User selects photos to be added to the custom game photo pool. 

-- FETCH RANDOM PHOTO FROM CUSTOM PHOTO POOL: 

SELECT cpp.photo_id, p.photo_data, p.room, p.floor, p.building
FROM custom_photo_pool cpp
INNER JOIN photo p ON cpp.photo_id = p.photo_id
WHERE cpp.custom_game_id = /* selected custom_game_id */
ORDER BY RAND()
LIMIT 1;

-- Returns a random photo from the selected custom game's photo pool.

-- INSERTING GUESS INTO GUESS TABLE: 

INSERT INTO guess (session_id, photo_id, guessed_room, guessed_floor, guessed_building, is_correct, proximity_score)
VALUES (/* session_id , photo_id , guessed_room , guessed_floor , guessed_building , 0 or 1 , calculated score */);

-- STORED PROCEDURE TO UPDATE GAME SESSION SCORE:

DELIMITER $$

CREATE PROCEDURE update_game_score(
    IN p_session_id INT,
    IN p_score INT
)
BEGIN
    -- Update total score for a normal game session
    UPDATE game_session
    SET total_score = total_score + p_score
    WHERE session_id = p_session_id;
END $$

DELIMITER ;

-- This procedure will likely be modified in the future to handle custom games as well. 

-- FETCH GLOBAL LEADERBOARD:

SELECT le.player_id, p.username, le.max_score, le.ranking
FROM leaderboard_entry le
INNER JOIN player p ON le.player_id = p.player_id
WHERE le.leaderboard_id = /* selected leaderboard_id */
ORDER BY le.ranking ASC;

-- Returns list of players, their usernames, scores, and rankings for the associated leaderboard. 

-- FETCH CUSTOM LEADERBOARD:

SELECT cle.custom_leaderboard_entry_id, p.username, cle.max_score, cle.ranking
FROM custom_leaderboard_entry cle
INNER JOIN player p ON cle.player_id = p.player_id
WHERE cle.custom_leaderboard_id = /* selected leaderboard_id */
ORDER BY cle.ranking ASC;

-- TRIGGER GLOBAL LEADERBOARD UPDATE AFTER GAME SESSION:

CREATE TRIGGER update_leaderboard_after_session
AFTER UPDATE ON game_session
FOR EACH ROW
BEGIN
    INSERT INTO leaderboard_entry (leaderboard_id, player_id, max_score)
    VALUES (/*global leaderboard id*/, NEW.player_id, NEW.total_score)
    ON DUPLICATE KEY UPDATE max_score = GREATEST(max_score, NEW.total_score);
END;

-- This will automatically update the leaderboard once the game session's total score changes. 
-- A similar trigger can be written for custom game sessions.
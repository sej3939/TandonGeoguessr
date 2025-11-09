-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 09, 2025 at 10:47 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `tandongeoguessr`
--

-- --------------------------------------------------------

--
-- Table structure for table `custom_game`
--

CREATE TABLE `custom_game` (
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `custom_game_session`
--

CREATE TABLE `custom_game_session` (
  `custom_session_id` int(11) NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `session_date` datetime NOT NULL DEFAULT current_timestamp(),
  `total_score` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `custom_leaderboard`
--

CREATE TABLE `custom_leaderboard` (
  `custom_leaderboard_id` int(10) UNSIGNED NOT NULL,
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `entry_count` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `custom_leaderboard_entry`
--

CREATE TABLE `custom_leaderboard_entry` (
  `custom_leaderboard_entry_id` int(10) UNSIGNED NOT NULL,
  `custom_leaderboard_id` int(10) UNSIGNED NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `max_score` int(10) UNSIGNED NOT NULL,
  `ranking` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `custom_photo_pool`
--

CREATE TABLE `custom_photo_pool` (
  `custom_photo_pool_id` int(10) UNSIGNED NOT NULL,
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `photo_id` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `game_session`
--

CREATE TABLE `game_session` (
  `session_id` int(10) UNSIGNED NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `session_date` datetime NOT NULL DEFAULT current_timestamp(),
  `total_score` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `guess`
--

CREATE TABLE `guess` (
  `guess_id` int(10) UNSIGNED NOT NULL,
  `session_id` int(10) UNSIGNED NOT NULL,
  `photo_id` int(10) UNSIGNED NOT NULL,
  `guessed_room` varchar(50) NOT NULL,
  `gueesed_floor` varchar(50) NOT NULL,
  `guessed_building` varchar(50) NOT NULL,
  `is_corrent` tinyint(1) NOT NULL,
  `proximity_score` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `leaderboard`
--

CREATE TABLE `leaderboard` (
  `leaderboard_id` int(10) UNSIGNED NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `entry_count` int(10) UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `leaderboard_entry`
--

CREATE TABLE `leaderboard_entry` (
  `entry_id` int(10) UNSIGNED NOT NULL,
  `leaderboard_id` int(10) UNSIGNED NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `max_score` int(10) UNSIGNED NOT NULL,
  `ranking` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `photo`
--

CREATE TABLE `photo` (
  `photo_id` int(10) UNSIGNED NOT NULL,
  `photo_data` longblob NOT NULL,
  `room` varchar(50) NOT NULL,
  `floor` varchar(50) NOT NULL,
  `building` varchar(50) NOT NULL,
  `upload_date` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `player`
--

CREATE TABLE `player` (
  `player_id` int(10) UNSIGNED NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `registration_date` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `custom_game`
--
ALTER TABLE `custom_game`
  ADD PRIMARY KEY (`custom_game_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indexes for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  ADD PRIMARY KEY (`custom_session_id`),
  ADD KEY `custom_game_id` (`custom_game_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indexes for table `custom_leaderboard`
--
ALTER TABLE `custom_leaderboard`
  ADD PRIMARY KEY (`custom_leaderboard_id`),
  ADD KEY `custom_game_id` (`custom_game_id`);

--
-- Indexes for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  ADD PRIMARY KEY (`custom_leaderboard_entry_id`),
  ADD KEY `player_id` (`player_id`),
  ADD KEY `custom_leaderboard_id` (`custom_leaderboard_id`);

--
-- Indexes for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  ADD PRIMARY KEY (`custom_photo_pool_id`),
  ADD KEY `custom_game_id` (`custom_game_id`),
  ADD KEY `photo_id` (`photo_id`);

--
-- Indexes for table `game_session`
--
ALTER TABLE `game_session`
  ADD PRIMARY KEY (`session_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indexes for table `guess`
--
ALTER TABLE `guess`
  ADD PRIMARY KEY (`guess_id`),
  ADD KEY `session_id` (`session_id`),
  ADD KEY `photo_id` (`photo_id`);

--
-- Indexes for table `leaderboard`
--
ALTER TABLE `leaderboard`
  ADD PRIMARY KEY (`leaderboard_id`);

--
-- Indexes for table `leaderboard_entry`
--
ALTER TABLE `leaderboard_entry`
  ADD PRIMARY KEY (`entry_id`),
  ADD KEY `player_id` (`player_id`),
  ADD KEY `leaderboard_id` (`leaderboard_id`);

--
-- Indexes for table `photo`
--
ALTER TABLE `photo`
  ADD PRIMARY KEY (`photo_id`);

--
-- Indexes for table `player`
--
ALTER TABLE `player`
  ADD PRIMARY KEY (`player_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `custom_game`
--
ALTER TABLE `custom_game`
  MODIFY `custom_game_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  MODIFY `custom_session_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `custom_leaderboard`
--
ALTER TABLE `custom_leaderboard`
  MODIFY `custom_leaderboard_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  MODIFY `custom_leaderboard_entry_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  MODIFY `custom_photo_pool_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `game_session`
--
ALTER TABLE `game_session`
  MODIFY `session_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `guess`
--
ALTER TABLE `guess`
  MODIFY `guess_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `leaderboard`
--
ALTER TABLE `leaderboard`
  MODIFY `leaderboard_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `leaderboard_entry`
--
ALTER TABLE `leaderboard_entry`
  MODIFY `entry_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `photo`
--
ALTER TABLE `photo`
  MODIFY `photo_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `player`
--
ALTER TABLE `player`
  MODIFY `player_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `custom_game`
--
ALTER TABLE `custom_game`
  ADD CONSTRAINT `custom_game_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);

--
-- Constraints for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  ADD CONSTRAINT `custom_game_session_ibfk_1` FOREIGN KEY (`custom_game_id`) REFERENCES `custom_game` (`custom_game_id`),
  ADD CONSTRAINT `custom_game_session_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);

--
-- Constraints for table `custom_leaderboard`
--
ALTER TABLE `custom_leaderboard`
  ADD CONSTRAINT `custom_leaderboard_ibfk_1` FOREIGN KEY (`custom_game_id`) REFERENCES `custom_game` (`custom_game_id`);

--
-- Constraints for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  ADD CONSTRAINT `custom_leaderboard_entry_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  ADD CONSTRAINT `custom_leaderboard_entry_ibfk_2` FOREIGN KEY (`custom_leaderboard_id`) REFERENCES `custom_leaderboard` (`custom_leaderboard_id`);

--
-- Constraints for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  ADD CONSTRAINT `custom_photo_pool_ibfk_1` FOREIGN KEY (`custom_game_id`) REFERENCES `custom_game` (`custom_game_id`),
  ADD CONSTRAINT `custom_photo_pool_ibfk_2` FOREIGN KEY (`photo_id`) REFERENCES `photo` (`photo_id`);

--
-- Constraints for table `game_session`
--
ALTER TABLE `game_session`
  ADD CONSTRAINT `game_session_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);

--
-- Constraints for table `guess`
--
ALTER TABLE `guess`
  ADD CONSTRAINT `guess_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `game_session` (`session_id`),
  ADD CONSTRAINT `guess_ibfk_2` FOREIGN KEY (`photo_id`) REFERENCES `photo` (`photo_id`);

--
-- Constraints for table `leaderboard_entry`
--
ALTER TABLE `leaderboard_entry`
  ADD CONSTRAINT `leaderboard_entry_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  ADD CONSTRAINT `leaderboard_entry_ibfk_2` FOREIGN KEY (`leaderboard_id`) REFERENCES `leaderboard` (`leaderboard_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

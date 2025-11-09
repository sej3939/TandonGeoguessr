-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 09, 2025 at 10:44 AM
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
-- Table structure for table `custom_game_session`
--

CREATE TABLE `custom_game_session` (
  `custom_session_id` int(11) NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `session_date` datetime NOT NULL DEFAULT current_timestamp(),
  `total_score` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  ADD PRIMARY KEY (`custom_session_id`),
  ADD KEY `custom_game_id` (`custom_game_id`),
  ADD KEY `player_id` (`player_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  MODIFY `custom_session_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `custom_game_session`
--
ALTER TABLE `custom_game_session`
  ADD CONSTRAINT `custom_game_session_ibfk_1` FOREIGN KEY (`custom_game_id`) REFERENCES `custom_game` (`custom_game_id`),
  ADD CONSTRAINT `custom_game_session_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

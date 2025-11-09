-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 09, 2025 at 10:45 AM
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
-- Table structure for table `custom_leaderboard_entry`
--

CREATE TABLE `custom_leaderboard_entry` (
  `custom_leaderboard_entry_id` int(10) UNSIGNED NOT NULL,
  `custom_leaderboard_id` int(10) UNSIGNED NOT NULL,
  `player_id` int(10) UNSIGNED NOT NULL,
  `max_score` int(10) UNSIGNED NOT NULL,
  `ranking` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  ADD PRIMARY KEY (`custom_leaderboard_entry_id`),
  ADD KEY `player_id` (`player_id`),
  ADD KEY `custom_leaderboard_id` (`custom_leaderboard_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  MODIFY `custom_leaderboard_entry_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `custom_leaderboard_entry`
--
ALTER TABLE `custom_leaderboard_entry`
  ADD CONSTRAINT `custom_leaderboard_entry_ibfk_1` FOREIGN KEY (`player_id`) REFERENCES `player` (`player_id`),
  ADD CONSTRAINT `custom_leaderboard_entry_ibfk_2` FOREIGN KEY (`custom_leaderboard_id`) REFERENCES `custom_leaderboard` (`custom_leaderboard_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

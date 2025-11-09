-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 09, 2025 at 10:46 AM
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
-- Table structure for table `custom_photo_pool`
--

CREATE TABLE `custom_photo_pool` (
  `custom_photo_pool_id` int(10) UNSIGNED NOT NULL,
  `custom_game_id` int(10) UNSIGNED NOT NULL,
  `photo_id` int(10) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  ADD PRIMARY KEY (`custom_photo_pool_id`),
  ADD KEY `custom_game_id` (`custom_game_id`),
  ADD KEY `photo_id` (`photo_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  MODIFY `custom_photo_pool_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `custom_photo_pool`
--
ALTER TABLE `custom_photo_pool`
  ADD CONSTRAINT `custom_photo_pool_ibfk_1` FOREIGN KEY (`custom_game_id`) REFERENCES `custom_game` (`custom_game_id`),
  ADD CONSTRAINT `custom_photo_pool_ibfk_2` FOREIGN KEY (`photo_id`) REFERENCES `photo` (`photo_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

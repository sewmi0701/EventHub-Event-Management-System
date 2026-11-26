-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 25, 2026 at 05:50 PM
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
-- Database: `eventhub_db`
-- This is a SANITIZED DEMONSTRATION EXPORT.
-- Original user accounts, personal email addresses and password hashes have been removed.
-- Import into a new / empty eventhub_db, not on top of your working database.
CREATE DATABASE IF NOT EXISTS `eventhub_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `eventhub_db`;
--

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `booking_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `booking_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` enum('confirmed','cancelled') NOT NULL DEFAULT 'confirmed'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- --------------------------------------------------------

--
-- Table structure for table `demo_payments`
--

CREATE TABLE `demo_payments` (
  `payment_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `status` varchar(30) NOT NULL DEFAULT 'demo_paid',
  `paid_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- --------------------------------------------------------

--
-- Table structure for table `events`
--

CREATE TABLE `events` (
  `event_id` int(11) NOT NULL,
  `organizer_id` int(11) NOT NULL,
  `title` varchar(150) NOT NULL,
  `category` varchar(50) NOT NULL,
  `event_date` date NOT NULL,
  `event_time` time NOT NULL,
  `location` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `max_participants` int(11) NOT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `status` enum('draft','published','cancelled') NOT NULL DEFAULT 'draft',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `ticket_price` decimal(10,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `notification_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `notification_type` varchar(40) NOT NULL,
  `title` varchar(160) NOT NULL,
  `message` text NOT NULL,
  `is_read` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','organizer','user') NOT NULL DEFAULT 'user',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
--
-- Indexes for dumped tables
--

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`booking_id`),
  ADD UNIQUE KEY `unique_booking` (`user_id`,`event_id`),
  ADD KEY `event_id` (`event_id`);

--
-- Indexes for table `demo_payments`
--
ALTER TABLE `demo_payments`
  ADD PRIMARY KEY (`payment_id`),
  ADD KEY `idx_demo_payment_booking` (`booking_id`),
  ADD KEY `idx_demo_payment_user` (`user_id`,`event_id`);

--
-- Indexes for table `events`
--
ALTER TABLE `events`
  ADD PRIMARY KEY (`event_id`),
  ADD KEY `organizer_id` (`organizer_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`notification_id`),
  ADD KEY `idx_notification_user` (`user_id`,`created_at`),
  ADD KEY `idx_notification_event` (`event_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `booking_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- AUTO_INCREMENT for table `demo_payments`
--
ALTER TABLE `demo_payments`
  MODIFY `payment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- AUTO_INCREMENT for table `events`
--
ALTER TABLE `events`
  MODIFY `event_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `notification_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`event_id`) REFERENCES `events` (`event_id`);

--
-- Constraints for table `events`
--
ALTER TABLE `events`
  ADD CONSTRAINT `events_ibfk_1` FOREIGN KEY (`organizer_id`) REFERENCES `users` (`user_id`);

-- =========================================
-- FICTIONAL SAMPLE RECORDS (safe to share)
-- Accounts are for an isolated local classroom demo only.
-- Change or remove them if deploying elsewhere.
-- =========================================
INSERT INTO `users` (`user_id`,`full_name`,`email`,`password_hash`,`role`) VALUES
(1,'Demo Administrator','admin-demo@example.com','scrypt:32768:8:1$7hY9nltXzA1cEPmx$9d33f2148b91c122523fbf3d48406f388fe213f47b83dfdf1e6b96dba095eed51dbcf9e271ab001498b9bd5074e59e6bc1ae49955235add2b8088268ad4f1d15','admin'),
(2,'Demo Organizer','organizer-demo@example.com','scrypt:32768:8:1$5EHOG9RdQqWwK8Kq$ec464a4a05d06d45f86f992cd157525735dc8e700ba54c2735e6a951e42401049e593df530ed29d66ae30dc74ce9eb86dcbadc334ef493e0c7ec840417fbe9a5','organizer'),
(3,'Demo Participant','participant-demo@example.com','scrypt:32768:8:1$KraUDmfKFYUrdtDh$8205fa582ce953c63fe14ff101a1ab71ca3f28e2b4c4e5ceb32dc35ada6d2a3a776b6e97aa33a4bf80d8c6aba18b9fb5748c5381624ba4ea39a4ba685c3814ef','user');

INSERT INTO `events` (`event_id`,`organizer_id`,`title`,`category`,`event_date`,`event_time`,`location`,`description`,`max_participants`,`image_path`,`status`,`ticket_price`) VALUES
(1,2,'Free Technology Meetup','Technology','2027-06-10','10:00:00','Colombo','Free demonstration event for EventHub.',40,NULL,'published',0.00),
(2,2,'Premium Technology Workshop','Technology','2027-08-15','11:00:00','Colombo','Paid demo workshop; no real payments are processed.',25,NULL,'published',1500.00);

INSERT INTO `bookings` (`booking_id`,`user_id`,`event_id`,`status`) VALUES
(1,3,1,'confirmed'),
(2,3,2,'confirmed');

INSERT INTO `demo_payments` (`payment_id`,`user_id`,`event_id`,`booking_id`,`amount`,`status`) VALUES
(1,3,2,2,1500.00,'demo_paid');

INSERT INTO `notifications` (`notification_id`,`user_id`,`event_id`,`notification_type`,`title`,`message`,`is_read`) VALUES
(1,3,1,'event_updated','Event Schedule Updated','The free event schedule has been updated for this demonstration.',1),
(2,3,2,'event_updated','Event Reminder','Your sample paid event booking is confirmed. This is only a demo record.',0);

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

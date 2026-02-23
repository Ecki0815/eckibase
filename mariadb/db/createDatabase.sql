-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Erstellungszeit: 23. Feb 2026 um 20:06
-- Server-Version: 10.11.13-MariaDB-0ubuntu0.24.04.1
-- PHP-Version: 8.4.16

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Datenbank: `home`
--
CREATE DATABASE IF NOT EXISTS `home` DEFAULT CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci;
USE `home`;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `HeatAndBright`
--

DROP TABLE IF EXISTS `HeatAndBright`;
CREATE TABLE IF NOT EXISTS `HeatAndBright` (
  `Datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `source` enum('bFloorDoor','bFloorSZ','bWc','bBath','bLiving','hOffice','hBath','hBed','hLiving','hOffice') NOT NULL,
  `value` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `Movement`
--

DROP TABLE IF EXISTS `Movement`;
CREATE TABLE IF NOT EXISTS `Movement` (
  `Datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `source` enum('mFloorDoor','mFloorSZ','mWc','mBath','mLiving') NOT NULL,
  `active` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `TempAndHum`
--

DROP TABLE IF EXISTS `TempAndHum`;
CREATE TABLE IF NOT EXISTS `TempAndHum` (
  `Datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `officeTemp` float NOT NULL,
  `badTemp` float NOT NULL,
  `wcTemp` float NOT NULL,
  `szTemp` float NOT NULL,
  `wzTemp` float NOT NULL,
  `floorTemp` float NOT NULL,
  `officeHum` float NOT NULL,
  `badHum` float NOT NULL,
  `wcHum` float NOT NULL,
  `szHum` float NOT NULL,
  `wzHum` float NOT NULL,
  `floorHum` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `Temperatures_old`
--

DROP TABLE IF EXISTS `Temperatures_old`;
CREATE TABLE IF NOT EXISTS `Temperatures_old` (
  `Datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `Office` float NOT NULL,
  `Bad` float NOT NULL,
  `SZ` float NOT NULL,
  `WZ` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;
COMMIT;

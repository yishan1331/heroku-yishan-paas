-- MySQL dump 10.16  Distrib 10.2.25-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: sapidoSystem
-- ------------------------------------------------------
-- Server version	10.2.25-MariaDB-10.2.25+maria~xenial-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `SOP`
--

DROP TABLE IF EXISTS `SOP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SOP` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部門編號',
  `title` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '大綱',
  `application` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用途',
  `filename` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'SOP檔案名稱',
  `path` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '存放路徑(88.100)',
  `level` tinyint(1) DEFAULT NULL COMMENT '權限等級(機密1/非機密0)',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='標準作業流程基本資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `department`
--

DROP TABLE IF EXISTS `department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `department` (
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `depName` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `noumenonType` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `noumenonID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `accessList` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `depInfo` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dbName` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp(),
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`depID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `meetingMinutes`
--

DROP TABLE IF EXISTS `meetingMinutes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `meetingMinutes` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部門編號',
  `date` date DEFAULT NULL COMMENT '會議日期',
  `title` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '會議主題',
  `filename` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '附加檔案名稱',
  `path` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '存放路徑(88.100)',
  `level` tinyint(1) NOT NULL COMMENT '權限等級(機密1/非機密0)',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='會議記錄資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `misBulletin`
--

DROP TABLE IF EXISTS `misBulletin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `misBulletin` (
  `seq` int(11) NOT NULL,
  `category` varchar(10) DEFAULT NULL,
  `title` varchar(128) DEFAULT NULL,
  `content` longtext DEFAULT NULL,
  `filename` longtext DEFAULT NULL,
  `showhide` tinyint(1) NOT NULL DEFAULT 1,
  `creatorID` varchar(10) DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp(),
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `section`
--

DROP TABLE IF EXISTS `section`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `section` (
  `secID` varchar(128) NOT NULL,
  `secName` varchar(128) DEFAULT NULL,
  `noumenonType` varchar(128) DEFAULT NULL,
  `noumenonID` varchar(128) DEFAULT NULL,
  `accessList` longtext DEFAULT NULL,
  `secInfo` varchar(256) DEFAULT NULL,
  `creatorID` varchar(10) DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp(),
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`secID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `server`
--

DROP TABLE IF EXISTS `server`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `server` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `status` tinyint(1) NOT NULL COMMENT '運作中 1/非運作中 0',
  `type` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Type',
  `manufacturer` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '製造商',
  `model` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '型號',
  `cpu` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'CPU',
  `memory` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '記憶體',
  `HDD` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'HDD',
  `NIC` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '網路卡(Network Interface Card)',
  `OS` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作業系統(Operating System)',
  `PM` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '實體機(Physical Machine)',
  `note` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Note',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='伺服器server基本資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `storage`
--

DROP TABLE IF EXISTS `storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `storage` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `species` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '種類(NAS or something)',
  `type` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '類型',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '名稱',
  `size` int(11) NOT NULL COMMENT 'SIZE(GB)',
  `subSize` int(11) NOT NULL COMMENT 'SUB SIZE(GB)',
  `note` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '內容說明',
  `IP` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '對應的server IP',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='儲存設備基本資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `todoList`
--

DROP TABLE IF EXISTS `todoList`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `todoList` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部門編號',
  `taskInfo` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '待辦事項描述',
  `taskDetail` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '執行細項',
  `schedDate` date DEFAULT NULL COMMENT '預計完成日期',
  `priority` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '優先順序',
  `assignTo` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '指派對象',
  `status` tinyint(1) NOT NULL COMMENT '狀態(1 完成/0 未完成)',
  `completedDate` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT '' COMMENT '實際完成日期',
  `startDate` date DEFAULT NULL COMMENT '發起日',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='待辦事項記錄資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `todoListComplt`
--

DROP TABLE IF EXISTS `todoListComplt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `todoListComplt` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '部門編號',
  `taskInfo` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '待辦事項描述',
  `taskDetail` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '執行細項',
  `schedDate` date DEFAULT NULL COMMENT '預計完成日期',
  `priority` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '優先順序',
  `assignTo` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '指派對象',
  `status` tinyint(1) NOT NULL COMMENT '狀態(1 完成/0 未完成)',
  `completedDate` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '實際完成日期',
  `startDate` date DEFAULT NULL COMMENT '發起日',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間(發起日)',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='已完成之待辦事項記錄資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `uID` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `pwd` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `uName` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `uInfo` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `noumenonType` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `noumenonID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `accessList` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp(),
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`uID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `virtualMachine`
--

DROP TABLE IF EXISTS `virtualMachine`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `virtualMachine` (
  `seq` int(11) NOT NULL COMMENT '編號',
  `noumenonID` int(11) NOT NULL COMMENT '隸屬server編號',
  `name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'VM名稱',
  `status` tinyint(1) NOT NULL COMMENT '狀態(已開啟電源 1/已關閉電源 0)',
  `provisionedSpace` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '佈建的空間',
  `usedSpace` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '已使用的空間',
  `memory` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '記憶體',
  `application` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用途',
  `property` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '性質',
  `installtionService` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '安裝服務(Installtion Service)',
  `computerName` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '電腦名稱',
  `OS` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作業系統(Operating System)',
  `systemLocation` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '系統位置',
  `privateIP` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '內部IP',
  `publicIP` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '對外IP',
  `port` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Port',
  `DM` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Disk保護機制(Defensive Mechanisms)',
  `remark` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '備註',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '創建者編號',
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='虛擬機virtual machine基本資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `weeklyReport`
--

DROP TABLE IF EXISTS `weeklyReport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `weeklyReport` (
  `seq` int(11) NOT NULL,
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `groupID` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` date DEFAULT NULL,
  `item` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `progress` int(11) DEFAULT NULL,
  `action` longtext COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `remark` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `priority` int(11) DEFAULT NULL COMMENT '排序(數字越小越重要)',
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='週報表記錄資料';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workedKey`
--

DROP TABLE IF EXISTS `workedKey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workedKey` (
  `seq` int(11) NOT NULL,
  `depID` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `groupID` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` date DEFAULT NULL,
  `item` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `detail` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creatorID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `createTime` timestamp NOT NULL DEFAULT current_timestamp() COMMENT '建立時間',
  `lastUpdateTime` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改時間',
  PRIMARY KEY (`seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作重點記錄資料';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-06-11 11:52:51

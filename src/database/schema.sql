CREATE DATABASE school_bus_scraper CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE school_bus_scraper;

-- Table: buses (Core Information)
CREATE TABLE `buses` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(256) DEFAULT NULL,
  `year` VARCHAR(10) DEFAULT NULL,
  `make` VARCHAR(25) DEFAULT NULL,
  `model` VARCHAR(50) DEFAULT NULL,
  `body` VARCHAR(25) DEFAULT NULL,
  `chassis` VARCHAR(25) DEFAULT NULL,
  `engine` VARCHAR(60) DEFAULT NULL,
  `transmission` VARCHAR(60) DEFAULT NULL,
  `mileage` VARCHAR(100) DEFAULT NULL,
  `passengers` VARCHAR(60) DEFAULT NULL,
  `wheelchair` VARCHAR(60) DEFAULT NULL,
  `color` VARCHAR(60) DEFAULT NULL,
  `interior_color` VARCHAR(60) DEFAULT NULL,
  `exterior_color` VARCHAR(60) DEFAULT NULL,
  `published` TINYINT(1) DEFAULT 0,
  `featured` TINYINT(1) DEFAULT 0,
  `sold` TINYINT(1) DEFAULT 0,
  `scraped` TINYINT(1) DEFAULT 0,
  `draft` TINYINT(1) DEFAULT 0,
  `source` VARCHAR(300) DEFAULT NULL,
  `source_url` VARCHAR(1000) DEFAULT NULL,
  `price` VARCHAR(30) DEFAULT NULL,
  `cprice` VARCHAR(30) DEFAULT NULL,
  `vin` VARCHAR(60) DEFAULT NULL,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `gvwr` VARCHAR(50) DEFAULT NULL,
  `dimensions` VARCHAR(300) DEFAULT NULL,
  `luggage` TINYINT(1) DEFAULT 0,
  `state_bus_standard` VARCHAR(25) DEFAULT NULL,
  `airconditioning` ENUM('REAR', 'DASH', 'BOTH', 'OTHER', 'NONE') DEFAULT 'NONE',
  `location` VARCHAR(30) DEFAULT NULL,
  `brake` VARCHAR(30) DEFAULT NULL,
  `contact_email` VARCHAR(100) DEFAULT NULL,
  `contact_phone` VARCHAR(100) DEFAULT NULL,
  `us_region` ENUM('NORTHEAST', 'MIDWEST', 'WEST', 'SOUTHWEST', 'SOUTHEAST', 'OTHER') DEFAULT 'OTHER',
  `description` LONGTEXT DEFAULT NULL,
  `score` TINYINT(1) DEFAULT 0,
  `category_id` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_bus_year` (`year`),
  KEY `idx_bus_make` (`make`),
  KEY `idx_bus_model` (`model`),
  KEY `idx_bus_price` (`price`),
  KEY `idx_bus_mileage` (`mileage`),
  KEY `idx_bus_location` (`location`),
  KEY `idx_bus_us_region` (`us_region`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- Table: buses_overview (Additional Information)
CREATE TABLE `buses_overview` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `bus_id` INT NOT NULL,
  `mdesc` LONGTEXT DEFAULT NULL,
  `intdesc` LONGTEXT DEFAULT NULL,
  `extdesc` LONGTEXT DEFAULT NULL,
  `features` LONGTEXT DEFAULT NULL,
  `specs` LONGTEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `busId` (`bus_id`),
  CONSTRAINT `buses_overview_ibfk_1` FOREIGN KEY (`bus_id`) REFERENCES `buses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- Table: buses_images (Images)
CREATE TABLE `buses_images` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(64) DEFAULT NULL,
  `url` VARCHAR(1000) DEFAULT NULL,
  `description` LONGTEXT DEFAULT NULL,
  `image_index` INT DEFAULT 0,
  `bus_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  KEY `busId` (`bus_id`) USING BTREE,
  CONSTRAINT `buses_images_ibfk_1` FOREIGN KEY (`bus_id`) REFERENCES `buses` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;
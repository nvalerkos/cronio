use contacts;

CREATE TABLE `contacts` (
  `pk` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(45) NOT NULL,
  `last_name` VARCHAR(45) NOT NULL,
  `tel` VARCHAR(45) NULL,
  PRIMARY KEY (`pk`));

INSERT INTO `contacts` (`first_name`, `last_name`, `tel`) VALUES ('John', 'Smith', '8138881901');
INSERT INTO `contacts` (`first_name`, `last_name`, `tel`) VALUES ('Jane', 'Smith', '8138881902');
INSERT INTO `contacts` (`first_name`, `last_name`, `tel`) VALUES ('Smithoui', 'Smith', '8138881903');

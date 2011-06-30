CREATE TABLE setl_localities
 (
	loc_id				SERIAL,
	loc_name			VARCHAR(100) NOT NULL UNIQUE,
	loc_nr				INTEGER,
	loc_coordinates		VARCHAR(100),
	loc_description		VARCHAR(300),

	CONSTRAINT loc_id_pk PRIMARY KEY (loc_id)
);

CREATE TABLE setl_species
 (
	spe_id					SERIAL,
	spe_name_venacular		VARCHAR(100) UNIQUE,
	spe_name_latin			VARCHAR(100) NOT NULL UNIQUE,
	spe_invasive_in_nl		BOOLEAN,
	spe_description			VARCHAR(300),
	spe_remarks				VARCHAR(160),
	spe_picture				OID,

	CONSTRAINT spe_id_pk PRIMARY KEY (spe_id)
);

CREATE TABLE setl_plates
 (
	pla_id					SERIAL,
	pla_loc_id				INTEGER NOT NULL,
	pla_setl_coordinator	VARCHAR(100),
	pla_nr					VARCHAR(100),
	pla_deployment_date		TIMESTAMP,
	pla_retrieval_date		TIMESTAMP,
	pla_water_temperature	VARCHAR(100),
	pla_salinity			VARCHAR(100),
	pla_visibility			VARCHAR(100),
	pla_remarks				VARCHAR(300),

	CONSTRAINT pla_id_pk PRIMARY KEY (pla_id),
	CONSTRAINT pla_loc_id_fk FOREIGN KEY (pla_loc_id)
		REFERENCES setl_localities (loc_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);

CREATE TABLE setl_records
 (
	rec_id				SERIAL,
	rec_pla_id			INTEGER NOT NULL,
	rec_spe_id			INTEGER NOT NULL,
	rec_unknown			BOOLEAN,
	rec_o				BOOLEAN,
	rec_r				BOOLEAN,
	rec_c				BOOLEAN,
	rec_a				BOOLEAN,
	rec_e				BOOLEAN,
	rec_sur_unknown		BOOLEAN,
	rec_sur1			BOOLEAN,
	rec_sur2			BOOLEAN,
	rec_sur3			BOOLEAN,
	rec_sur4			BOOLEAN,
	rec_sur5			BOOLEAN,
	rec_sur6			BOOLEAN,
	rec_sur7			BOOLEAN,
	rec_sur8			BOOLEAN,
	rec_sur9			BOOLEAN,
	rec_sur10			BOOLEAN,
	rec_sur11			BOOLEAN,
	rec_sur12			BOOLEAN,
	rec_sur13			BOOLEAN,
	rec_sur14			BOOLEAN,
	rec_sur15			BOOLEAN,
	rec_sur16			BOOLEAN,
	rec_sur17			BOOLEAN,
	rec_sur18			BOOLEAN,
	rec_sur19			BOOLEAN,
	rec_sur20			BOOLEAN,
	rec_sur21			BOOLEAN,
	rec_sur22			BOOLEAN,
	rec_sur23			BOOLEAN,
	rec_sur24			BOOLEAN,
	rec_sur25			BOOLEAN,
	rec_1st				BOOLEAN,
	rec_2nd				BOOLEAN,
	rec_v				BOOLEAN,
	rec_photo_nrs		VARCHAR(100),
	rec_remarks			VARCHAR(100),

	CONSTRAINT rec_id_pk PRIMARY KEY (rec_id),
	CONSTRAINT rec_pla_id_fk FOREIGN KEY (rec_pla_id)
		REFERENCES setl_plates (pla_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION,
	CONSTRAINT rec_spe_id_fk FOREIGN KEY (rec_spe_id)
		REFERENCES setl_species (spe_id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);


COPY setl_localities FROM '/home/serrano/Gimaris/Serrano/head/database/csv_processed/setl_localities.csv' DELIMITER ',' CSV HEADER;
COPY setl_plates FROM '/home/serrano/Gimaris/Serrano/head/database/csv_processed/setl_plates.csv' DELIMITER ',' CSV HEADER;
COPY setl_records FROM '/home/serrano/Gimaris/Serrano/head/database/csv_processed/setl_records.csv' DELIMITER ',' CSV HEADER;
COPY setl_species FROM '/home/serrano/Gimaris/Serrano/head/database/csv_processed/setl_species.csv' DELIMITER ',' CSV HEADER;

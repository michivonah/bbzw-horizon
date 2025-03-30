INSERT INTO "user" ("name", "api_access") VALUES
	('test', True);
	
INSERT INTO "sessions" ("token", "userid", "validuntil") VALUES
	('test2', 1, '2025-04-30');
	
INSERT INTO "clients" ("name") VALUES
	('1.54');

INSERT INTO "user" ("name", "api_access", "password") VALUES
	('sepp', True, '473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8'); -- PASSWORD: string

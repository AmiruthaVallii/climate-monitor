INSERT INTO flood_severity (severity_level,severity_name, severity_meaning)
    VALUES (1, 'Severe Flood Warning','Severe Flooding, Danger to Life.'),
           (2,'Flood Warning','Flooding is Expected, Immediate Action Required.'),
           (3,'Flood Alert', 'Flooding is Possible, Be Prepared.'),
           (4,'Warning no Longer in Force','The warning is no longer in force');


INSERT INTO locations(location_name,latitude,longitude)
    VALUES('London',51.507351,-0.127758),
          ('Plymouth',50.371842,-4.183685),
          ('Birmingham',52.482899,-1.893460),
          ('Cardiff',51.481583,-3.179090),
          ('Aberystwyth',52.416119,-4.083800),
          ('Manchester',53.480759,-2.242631),
          ('Leeds',53.800755,-1.549077),
          ('Newcastle',54.978252,-1.617780),
          ('Glasgow',55.864239,-4.251806),
          ('Edinburgh',55.953251,-3.188267),
          ('Aberdeen',57.147480,-2.095400),
          ('Inverness',57.477772,-4.224721),
          ('Belfast',54.597286,-5.930120),
          ('Derry',54.996613,-7.308575);
USE smart_house;

INSERT INTO devices (id, name, status) VALUES
    (1, 'LED 1', 'OFF'),
    (2, 'LED 2', 'OFF');

INSERT INTO sensors (id, name, unit, min_normal, max_normal) VALUES
    (1, 'Temperature', '°C', 18, 35),
    (2, 'Humidity', '%', 40, 80),
    (3, 'Light', 'lux', 100, 800);
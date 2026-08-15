-- Seed Tamil News Sources
INSERT INTO sources (name, domain, language, orientation, orientation_confidence, orientation_evidence, last_reviewed) VALUES
('Dina Thanthi', 'dailythanthi.com', 'ta', 'POPULIST_SENSATIONAL', 0.85, 'Analysis of editorial content over the last year shows preference for sensationalist headlines.', NOW()),
('Dinamalar', 'dinamalar.com', 'ta', 'CONSERVATIVE_VARIABLE', 0.80, 'Historically conservative editorial stance on economic and social issues.', NOW()),
('Dinakaran', 'dinakaran.com', 'ta', 'DRAVIDIAN_ORIENTED', 0.90, 'Clear alignment with Dravidian ideology in op-eds and story selection.', NOW()),
('Maalai Malar', 'maalaimalar.com', 'ta', 'POPULIST_SENSATIONAL', 0.80, 'Evening daily focused on quick news with sensational framing.', NOW()),
('Namadhu Amma', 'namadhuamma.com', 'ta', 'AIADMK_ORIENTED', 0.95, 'Official party organ of AIADMK.', NOW());

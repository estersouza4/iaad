-- ARQUIVO CONSOLIDADO PARA ENTREGA
-- ATENCAO: este script usa DROP DATABASE IF EXISTS torneio_robotica;
-- Executa-lo apaga e recria o banco torneio_robotica e seus dados.
-- Guarde um backup e execute somente quando desejar reconstruir do zero.

-- =====================================================================
-- Banco de Dados: Torneio de Robótica
-- Disciplina: IAAD - 2ª VA - Atividade 1
-- Tabelas: equipe, robo, resultado (do DER) + integrante (nova)
-- =====================================================================

DROP DATABASE IF EXISTS torneio_robotica;
CREATE DATABASE torneio_robotica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE torneio_robotica;

-- ---------------------------------------------------------------------
-- 1) EQUIPE
-- ---------------------------------------------------------------------
CREATE TABLE equipe (
    id_equipe   INT AUTO_INCREMENT PRIMARY KEY,
    nome_equipe VARCHAR(100) NOT NULL,
    escola      VARCHAR(100) NOT NULL,
    cidade      VARCHAR(80)  NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2) INTEGRANTE (NOVA) - equipe 1 --- N integrante
--    Apagar/atualizar a equipe propaga para os integrantes (CASCADE)
-- ---------------------------------------------------------------------
CREATE TABLE integrante (
    id_integrante   INT AUTO_INCREMENT PRIMARY KEY,
    nome_integrante VARCHAR(100) NOT NULL,
    funcao          VARCHAR(50)  NOT NULL,   -- ex.: Programador, Piloto, Mecânico
    data_nascimento DATE,
    id_equipe       INT NOT NULL,
    CONSTRAINT fk_integrante_equipe
        FOREIGN KEY (id_equipe) REFERENCES equipe (id_equipe)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3) ROBO - equipe 1 --- N robo
--    RESTRICT no DELETE: não deixa apagar equipe que tenha robô
--    (usado no vídeo para mostrar violação de integridade referencial).
-- ---------------------------------------------------------------------
CREATE TABLE robo (
    id_robo      INT AUTO_INCREMENT PRIMARY KEY,
    nome_robo    VARCHAR(100) NOT NULL,
    categoria    VARCHAR(50)  NOT NULL,      -- ex.: Sumô, Seguidor de Linha
    data_criacao DATE,
    id_equipe    INT NOT NULL,
    CONSTRAINT fk_robo_equipe
        FOREIGN KEY (id_equipe) REFERENCES equipe (id_equipe)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4) RESULTADO - robo 1 --- N resultado
--    PK composta (nome_prova, classificacao), como no DER:
--    em cada prova, cada posição na classificação é ocupada por 1 robô.
-- ---------------------------------------------------------------------
CREATE TABLE resultado (
    nome_prova    VARCHAR(100) NOT NULL,
    classificacao INT          NOT NULL,
    pontuacao     DECIMAL(6,2) NOT NULL,
    id_robo       INT          NOT NULL,
    PRIMARY KEY (nome_prova, classificacao),
    CONSTRAINT fk_resultado_robo
        FOREIGN KEY (id_robo) REFERENCES robo (id_robo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- =====================================================================
-- CARGA DE DADOS
-- =====================================================================
INSERT INTO equipe (nome_equipe, escola, cidade) VALUES
('Os Autômatos',   'Escola Técnica Estadual Porto Digital', 'Recife'),
('Circuito Veloz', 'Colégio Municipal Clarice Lispector',   'Olinda'),
('Byte Warriors',  'Instituto Federal de Pernambuco',       'Jaboatão dos Guararapes'),
('Robô Sertão',    'Escola Técnica de Caruaru',             'Caruaru');

INSERT INTO integrante (nome_integrante, funcao, data_nascimento, id_equipe) VALUES
('Ana Beatriz Silva',   'Programadora', '2008-03-14', 1),
('Carlos Eduardo Lima', 'Mecânico',     '2007-11-02', 1),
('Mariana Souza',       'Piloto',       '2008-07-21', 2),
('João Pedro Alves',    'Programador',  '2007-05-30', 2),
('Fernanda Costa',      'Eletrônica',   '2008-01-09', 3),
('Rafael Mendes',       'Piloto',       '2007-09-17', 3),
('Larissa Oliveira',    'Programadora', '2008-12-05', 4),
('Gabriel Santos',      'Mecânico',     '2007-04-25', 4);

INSERT INTO robo (nome_robo, categoria, data_criacao, id_equipe) VALUES
('Titan',      'Sumô',              '2026-02-10', 1),
('Faísca',     'Seguidor de Linha', '2026-03-05', 1),
('Relâmpago',  'Seguidor de Linha', '2026-01-20', 2),
('Mamute',     'Sumô',              '2026-02-28', 2),
('Cyber-Lobo', 'Sumô',              '2026-03-15', 3),
('Cangaceiro', 'Seguidor de Linha', '2026-04-01', 4),
('Mandacaru',  'Sumô',              '2026-04-12', 4);   -- ainda sem resultado

INSERT INTO resultado (nome_prova, classificacao, pontuacao, id_robo) VALUES
('Sumô de Robôs',     1, 97.75, 4),   -- Mamute
('Sumô de Robôs',     2, 90.00, 1),   -- Titan
('Sumô de Robôs',     3, 72.25, 5),   -- Cyber-Lobo
('Seguidor de Linha', 1, 94.10, 3),   -- Relâmpago
('Seguidor de Linha', 2, 86.30, 2),   -- Faísca
('Seguidor de Linha', 3, 65.80, 6);   -- Cangaceiro

-- =====================================================================
-- CONSULTAS NÃO TRIVIAIS (exemplos para usar/adaptar no sistema web)
-- =====================================================================

-- Q1) Pontuação média, máxima e nº de participações por equipe
--     (JOIN + GROUP BY + agregações)
-- SELECT  e.nome_equipe,
--         COUNT(r.classificacao)     AS participacoes,
--         ROUND(AVG(r.pontuacao),2)  AS media_pontuacao,
--         MAX(r.pontuacao)           AS melhor_pontuacao
-- FROM    equipe e
--         JOIN robo ro     ON ro.id_equipe = e.id_equipe
--         JOIN resultado r ON r.id_robo    = ro.id_robo
-- GROUP BY e.id_equipe, e.nome_equipe
-- ORDER BY media_pontuacao DESC;

-- Q2) Robôs que ainda NÃO competiram (LEFT JOIN exclusivo)
-- SELECT  ro.nome_robo, ro.categoria, e.nome_equipe
-- FROM    robo ro
--         JOIN equipe e ON e.id_equipe = ro.id_equipe
--         LEFT JOIN resultado r ON r.id_robo = ro.id_robo
-- WHERE   r.id_robo IS NULL;

-- Q3) Equipes, nº de integrantes e idade média
--     (LEFT JOIN + COUNT + manipulação de datas)
-- SELECT  e.nome_equipe,
--         COUNT(i.id_integrante) AS qtd_integrantes,
--         ROUND(AVG(TIMESTAMPDIFF(YEAR, i.data_nascimento, CURDATE())),1) AS idade_media
-- FROM    equipe e
--         LEFT JOIN integrante i ON i.id_equipe = e.id_equipe
-- GROUP BY e.id_equipe, e.nome_equipe;

-- =====================================================================
-- ROTEIRO DE DEMONSTRAÇÃO DE INTEGRIDADE REFERENCIAL (para o vídeo)
-- =====================================================================
-- (a) Violação de FK (equipe inexistente):
--     INSERT INTO robo (nome_robo, categoria, data_criacao, id_equipe)
--     VALUES ('Fantasma', 'Sumô', '2026-05-01', 999);
--
-- (b) RESTRICT: apagar equipe que tem robô
--     DELETE FROM equipe WHERE id_equipe = 1;                -- erro
--
-- (c) CASCADE no DELETE: apagar robô remove seus resultados
--     DELETE FROM robo WHERE id_robo = 3;
--
-- (d) CASCADE no UPDATE: mudar o id do robô propaga para resultado
--     UPDATE robo SET id_robo = 30 WHERE id_robo = 6;
--
-- (e) PK composta: repetir (prova, classificação)
--     INSERT INTO resultado VALUES ('Sumô de Robôs', 1, 80.00, 1);  -- erro
-- =====================================================================

-- =====================================================================
-- FUNCIONALIDADES DESENVOLVIDAS E TESTADAS
-- =====================================================================

-- CONSULTA ELABORADA: desempenho por equipe
-- JOIN + GROUP BY + COUNT, SUM, AVG e MAX
SELECT
    e.nome_equipe AS equipe,
    COUNT(DISTINCT ro.id_robo) AS quantidade_robos,
    COUNT(r.id_robo) AS participacoes,
    COALESCE(SUM(r.pontuacao), 0) AS pontuacao_total,
    ROUND(AVG(r.pontuacao), 2) AS pontuacao_media,
    MAX(r.pontuacao) AS maior_pontuacao
FROM equipe e
LEFT JOIN robo ro ON e.id_equipe = ro.id_equipe
LEFT JOIN resultado r ON ro.id_robo = r.id_robo
GROUP BY e.id_equipe, e.nome_equipe
ORDER BY pontuacao_total DESC;

-- TRIGGER: impede pontuacao negativa no INSERT
DELIMITER $$
CREATE TRIGGER trg_validar_pontuacao
BEFORE INSERT ON resultado
FOR EACH ROW
BEGIN
    IF NEW.pontuacao < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Erro: a pontuacao nao pode ser negativa.';
    END IF;
END$$
DELIMITER ;

-- PROCEDURE: consulta de desempenho a partir do identificador de equipe
DELIMITER $$
CREATE PROCEDURE sp_desempenho_equipe(IN p_id_equipe INT)
BEGIN
    SELECT
        e.id_equipe,
        e.nome_equipe,
        COUNT(DISTINCT ro.id_robo) AS quantidade_robos,
        COUNT(r.id_robo) AS participacoes,
        COALESCE(SUM(r.pontuacao), 0) AS pontuacao_total,
        ROUND(AVG(r.pontuacao), 2) AS pontuacao_media,
        MAX(r.pontuacao) AS maior_pontuacao
    FROM equipe e
    LEFT JOIN robo ro ON e.id_equipe = ro.id_equipe
    LEFT JOIN resultado r ON ro.id_robo = r.id_robo
    WHERE e.id_equipe = p_id_equipe
    GROUP BY e.id_equipe, e.nome_equipe;
END$$
DELIMITER ;

-- Exemplo de uso da procedure (descomente para testar):
-- CALL sp_desempenho_equipe(2);

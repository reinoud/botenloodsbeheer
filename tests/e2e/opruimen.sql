-- Ruimt na een E2E-run op wat aantoonbaar van een E2E-run is (issue #142). Draait in draai.sh als
-- eigenaar van de database, in de db-container van de dev-stack, in één transactie: een fout
-- laat alles staan. Geen applicatiecode; de logregels blijven staan (besluit 2026-11-06).
--
-- Kenmerk van een run: de stempel. Een stempel is bekend als er een beheerder `e2e-<soort>-<stempel>`
-- of een token `e2e-<soort>-<stempel>[-n]` met die stempel is, of als draai.sh hem meegeeft
-- (-v stempel=...). Wat niet aan een bekende stempel hangt, blijft staan en wordt gemeld.
--   rek         <letter> + stempel in 36-tallig (reknaam() in conftest.py); plaatsen gaan mee
--   boot        naam eindigt op een spatie plus de stempel of zo'n reknaam; foto en wachtlijstregel mee
--   bootsoort   "Waterfiets <stempel>" en "Pedalo <stempel>" (test_bootsoorten.py)
--   token, beheerder   naam met de stempel; uitnodiging en passkeys gaan mee (ON DELETE CASCADE)
\set ON_ERROR_STOP on
BEGIN;
SELECT set_config('e2e.stempel', :'stempel', true) \g /dev/null
DO $$
DECLARE
    n_plaats int; n_boot int; n_foto int; n_soort int; n_rek int; n_token int; n_beheerder int;
    rest text;
BEGIN
    CREATE TEMP TABLE e2e_stempel ON COMMIT DROP AS
        SELECT DISTINCT s FROM (
            SELECT substring(gebruikersnaam from '^e2e-[a-z]+-([0-9]{9,10})$') AS s FROM beheerder
            UNION SELECT substring(naam from '^e2e-[a-z]+-([0-9]{9,10})(-[0-9]+)?$') FROM token
            UNION SELECT current_setting('e2e.stempel')
        ) x WHERE s ~ '^[0-9]{9,10}$';

    CREATE TEMP TABLE e2e_b36 ON COMMIT DROP AS
        WITH RECURSIVE b(s, n, r) AS (
            SELECT s, s::bigint, '' FROM e2e_stempel
            UNION ALL
            SELECT s, n / 36, substr('0123456789abcdefghijklmnopqrstuvwxyz', (n % 36)::int + 1, 1) || r
            FROM b WHERE n > 0)
        SELECT s, r AS b36 FROM b WHERE n = 0;

    CREATE TEMP TABLE e2e_rek ON COMMIT DROP AS
        SELECT rek.id FROM rek JOIN e2e_b36 ON lower(rek.naam) ~ ('^[a-z]' || b36 || '$');

    CREATE TEMP TABLE e2e_boot ON COMMIT DROP AS
        SELECT boot.id, boot.afbeelding_id FROM boot
        WHERE EXISTS (SELECT 1 FROM e2e_stempel WHERE boot.naam ~ (' ' || s || '$'))
           OR EXISTS (SELECT 1 FROM e2e_b36 WHERE boot.naam ~ (' [a-z]' || b36 || '$'));

    -- Een boot die niet van de run is maar op een rek van de run staat: niets doen.
    IF EXISTS (SELECT 1 FROM plaats WHERE rek_id IN (SELECT id FROM e2e_rek)
               AND boot_id IS NOT NULL AND boot_id NOT IN (SELECT id FROM e2e_boot)) THEN
        RAISE EXCEPTION 'Een rek van een E2E-run bevat een boot zonder E2E-kenmerk; niets opgeruimd.';
    END IF;

    DELETE FROM plaats WHERE rek_id IN (SELECT id FROM e2e_rek);
    GET DIAGNOSTICS n_plaats = ROW_COUNT;
    DELETE FROM boot WHERE id IN (SELECT id FROM e2e_boot);
    GET DIAGNOSTICS n_boot = ROW_COUNT;
    DELETE FROM afbeelding WHERE id IN (SELECT afbeelding_id FROM e2e_boot);
    GET DIAGNOSTICS n_foto = ROW_COUNT;
    DELETE FROM bootsoort WHERE EXISTS (
        SELECT 1 FROM e2e_stempel WHERE bootsoort.naam ~ ('^(Waterfiets|Pedalo) ' || s || '$'));
    GET DIAGNOSTICS n_soort = ROW_COUNT;
    DELETE FROM rek WHERE id IN (SELECT id FROM e2e_rek);
    GET DIAGNOSTICS n_rek = ROW_COUNT;
    DELETE FROM token WHERE EXISTS (
        SELECT 1 FROM e2e_stempel WHERE token.naam ~ ('^e2e-[a-z]+-' || s || '(-[0-9]+)?$'));
    GET DIAGNOSTICS n_token = ROW_COUNT;
    DELETE FROM beheerder WHERE EXISTS (
        SELECT 1 FROM e2e_stempel WHERE beheerder.gebruikersnaam ~ ('^e2e-[a-z]+-' || s || '$'));
    GET DIAGNOSTICS n_beheerder = ROW_COUNT;

    RAISE NOTICE 'Opgeruimd: % rekken, % plaatsen, % boten, % foto''s, % bootsoorten, % tokens, % beheerders',
        n_rek, n_plaats, n_boot, n_foto, n_soort, n_token, n_beheerder;

    -- Wat op een E2E-rest lijkt maar niet aan een bekende stempel hangt: laten staan en melden.
    SELECT string_agg(naam, ', ') INTO rest FROM rek WHERE naam ~ '^[a-z][0-9a-z]{6}$';
    IF rest IS NOT NULL THEN RAISE NOTICE 'Twijfel, laten staan (rekken): %', rest; END IF;
    SELECT string_agg(gebruikersnaam, ', ') INTO rest FROM beheerder WHERE gebruikersnaam LIKE 'e2e-%';
    IF rest IS NOT NULL THEN RAISE NOTICE 'Twijfel, laten staan (beheerders): %', rest; END IF;
    SELECT string_agg(naam, ', ') INTO rest FROM token WHERE naam LIKE 'e2e-%';
    IF rest IS NOT NULL THEN RAISE NOTICE 'Twijfel, laten staan (tokens): %', rest; END IF;
END $$;
COMMIT;

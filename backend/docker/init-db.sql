-- Postgres 컨테이너 최초 실행 시 자동 실행
-- tft_meta DB는 POSTGRES_DB 환경변수로 이미 생성됨
-- airflow DB 추가 생성
SELECT 'CREATE DATABASE airflow OWNER tft_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

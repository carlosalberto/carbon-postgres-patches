--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: daily_stats; Type: TABLE; Schema: public; Owner: ; Tablespace: 
--

CREATE TABLE daily_stats (
    id integer NOT NULL,
    name character(100) NOT NULL,
    value double precision NOT NULL,
    day timestamp with time zone NOT NULL
);


--
-- Name: daily_stats_id_seq; Type: SEQUENCE; Schema: public; Owner:
--

CREATE SEQUENCE daily_stats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: daily_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner:
--

ALTER SEQUENCE daily_stats_id_seq OWNED BY daily_stats.id;


--
-- Name: daily_stats_id_seq; Type: SEQUENCE SET; Schema: public; Owner:
--

SELECT pg_catalog.setval('daily_stats_id_seq', 4, true);


--
-- Name: latest_stats; Type: TABLE; Schema: public; Owner: ; Tablespace: 
--

CREATE TABLE latest_stats (
    id integer NOT NULL,
    name character(100),
    value double precision,
    tstamp timestamp with time zone
);


--
-- Name: latest_stats_id_seq; Type: SEQUENCE; Schema: public; Owner:
--

CREATE SEQUENCE latest_stats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: latest_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner:
--

ALTER SEQUENCE latest_stats_id_seq OWNED BY latest_stats.id;


--
-- Name: latest_stats_id_seq; Type: SEQUENCE SET; Schema: public; Owner: 
--

SELECT pg_catalog.setval('latest_stats_id_seq', 4615, true);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY daily_stats ALTER COLUMN id SET DEFAULT nextval('daily_stats_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: 
--

ALTER TABLE ONLY latest_stats ALTER COLUMN id SET DEFAULT nextval('latest_stats_id_seq'::regclass);


--
-- Data for Name: daily_stats; Type: TABLE DATA; Schema: public; Owner: 
--

COPY daily_stats (id, name, value, day) FROM stdin;
\.


--
-- Data for Name: latest_stats; Type: TABLE DATA; Schema: public; Owner: statsd
--

COPY latest_stats (id, name, value, tstamp) FROM stdin;
\.


--
-- Name: daily_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: statsd; Tablespace: 
--

ALTER TABLE ONLY daily_stats
    ADD CONSTRAINT daily_stats_pkey PRIMARY KEY (id);


--
-- Name: latest_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: statsd; Tablespace: 
--

ALTER TABLE ONLY latest_stats
    ADD CONSTRAINT latest_stats_pkey PRIMARY KEY (id);

--
-- PostgreSQL database dump complete
--


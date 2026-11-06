CREATE SCHEMA public;
CREATE SCHEMA billing;
CREATE TABLE public.customers (
 customer_id uuid PRIMARY KEY,
 name varchar(80) NOT NULL
);
CREATE TABLE public.orders (
 order_id uuid PRIMARY KEY,
 customer_id uuid NOT NULL REFERENCES public.customers(customer_id),
 status varchar(20) NOT NULL
);
CREATE TABLE billing.receipts (
 receipt_id uuid PRIMARY KEY,
 order_id uuid NOT NULL REFERENCES public.orders(order_id)
);

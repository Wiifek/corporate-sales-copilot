---
doc_id: metrics_glossary
doc_type: glossary
title: Metrics Glossary
languages: [en, fr]
---

# Metrics Glossary

Every metric below follows the same structure: name, French name, definition, formula,
where it is shown, pitfalls, and a SQL example that runs on the dataset.
Unless stated otherwise, a **non-cancelled ticket** means `status <> 'cancelled'`
(so it includes `flown` and `upcoming` tickets), and periods are based on `booking_date`.

## Metrics

### Booked net revenue
- **French name:** Chiffre d'affaires net réservé
- **Definition:** Total of the net fares (after contract discount) of all non-cancelled tickets, assigned to the period in which the ticket was **booked**. This is the reference revenue metric of the Corporate Sales team, and the one used to measure targets.
- **Définition (FR):** Somme des tarifs nets (après remise contractuelle) des billets non annulés, rattachée à la période de réservation. C'est le chiffre d'affaires de référence, celui des objectifs.
- **Formula:** `sum(net_fare_eur)` where `status <> 'cancelled'`, filtered on `booking_date`.
- **Unit:** EUR
- **Shown in:** Account Performance, Route & Cabin Revenue, Targets & Contract Compliance
- **Pitfalls:** Cancelled tickets are excluded. It includes tickets not yet flown (`upcoming`). Do not filter on `travel_date`: that gives a different metric (see Flown net revenue). Taxes and ancillaries are not in the data.

```sql
SELECT a.sales_region,
       round(sum(b.net_fare_eur)) AS booked_net_revenue_eur
FROM bookings b
JOIN accounts a USING (account_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Flown net revenue
- **French name:** Chiffre d'affaires net volé
- **Definition:** Total of the net fares of tickets whose trip has already taken place (`status = 'flown'`), assigned to the period of **travel**, not of booking.
- **Définition (FR):** Somme des tarifs nets des billets dont le vol a déjà eu lieu, rattachée à la période du voyage.
- **Formula:** `sum(net_fare_eur)` where `status = 'flown'`, filtered on `travel_date`.
- **Unit:** EUR
- **Shown in:** None (available by querying the data only)
- **Pitfalls:** It is lower than Booked net revenue for the same period because upcoming tickets are not counted. Tickets with a travel date after the as-of date (2026-09-30) are `upcoming`, so recent months look incomplete.

```sql
SELECT a.sales_region,
       round(sum(b.net_fare_eur)) AS flown_net_revenue_eur
FROM bookings b
JOIN accounts a USING (account_id)
WHERE b.status = 'flown'
  AND year(b.travel_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Gross revenue
- **French name:** Chiffre d'affaires brut
- **Definition:** Total of the gross fares (public price before contract discount) of all non-cancelled tickets, by booking period.
- **Définition (FR):** Somme des tarifs bruts (avant remise contractuelle) des billets non annulés, par période de réservation.
- **Formula:** `sum(gross_fare_eur)` where `status <> 'cancelled'`.
- **Unit:** EUR
- **Shown in:** None (available by querying the data only)
- **Pitfalls:** Gross minus net equals the discount granted to customers. Never use gross revenue to measure targets: targets are set on net revenue.

```sql
SELECT a.size_tier,
       round(sum(b.gross_fare_eur)) AS gross_revenue_eur
FROM bookings b
JOIN accounts a USING (account_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Tickets sold
- **French name:** Billets vendus
- **Definition:** Number of non-cancelled tickets. One booking row is one ticket (one passenger, one one-way flight).
- **Définition (FR):** Nombre de billets non annulés. Une ligne de réservation correspond à un billet (un passager, un vol aller simple).
- **Formula:** `count(*)` where `status <> 'cancelled'`.
- **Unit:** tickets
- **Shown in:** Account Performance, Route & Cabin Revenue, Targets & Contract Compliance
- **Pitfalls:** A round trip counts as two tickets. Cancelled tickets are not counted.

```sql
SELECT r.market_region,
       count(*) AS tickets_sold
FROM bookings b
JOIN routes r USING (route_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Average net fare
- **French name:** Tarif net moyen
- **Definition:** Booked net revenue divided by tickets sold: the average price paid per ticket after discount.
- **Définition (FR):** Chiffre d'affaires net réservé divisé par le nombre de billets vendus.
- **Formula:** `sum(net_fare_eur) / count(*)` where `status <> 'cancelled'`.
- **Unit:** EUR per ticket
- **Shown in:** Account Performance, Route & Cabin Revenue
- **Pitfalls:** Strongly affected by the mix of routes and cabins. A higher average can simply mean more long-haul or Business tickets, not higher prices. Compare within the same haul and cabin.

```sql
SELECT r.haul, b.cabin,
       round(avg(b.net_fare_eur)) AS average_net_fare_eur
FROM bookings b
JOIN routes r USING (route_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Effective discount rate
- **French name:** Taux de remise effectif
- **Definition:** Share of the gross fare that was given back as discount: (gross revenue − net revenue) ÷ gross revenue, over non-cancelled tickets.
- **Définition (FR):** Part du tarif brut accordée en remise : (CA brut − CA net) ÷ CA brut, sur les billets non annulés.
- **Formula:** `1 - sum(net_fare_eur) / sum(gross_fare_eur)` where `status <> 'cancelled'`.
- **Unit:** percent
- **Shown in:** Account Performance
- **Pitfalls:** For one account it equals the contract discount (`contracts.discount_pct`), because the same discount applies to all its tickets. For a group of accounts (region, tier, industry) it is the average weighted by fares, so it is not the simple average of contract discounts.

```sql
SELECT a.size_tier,
       round(100 * (1 - sum(b.net_fare_eur) / sum(b.gross_fare_eur)), 1) AS effective_discount_rate_pct
FROM bookings b
JOIN accounts a USING (account_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Cancellation rate
- **French name:** Taux d'annulation
- **Definition:** Share of bookings that were cancelled: cancelled tickets ÷ all tickets booked in the period.
- **Définition (FR):** Part des réservations annulées : billets annulés ÷ ensemble des billets réservés sur la période.
- **Formula:** `avg((status = 'cancelled')::INT)` over **all** bookings, filtered on `booking_date`.
- **Unit:** percent
- **Shown in:** Account Performance
- **Pitfalls:** The denominator includes cancelled bookings, unlike Tickets sold. It is computed on the number of tickets, not on revenue.

```sql
SELECT a.sales_region,
       round(100 * avg((b.status = 'cancelled')::INT), 1) AS cancellation_rate_pct
FROM bookings b
JOIN accounts a USING (account_id)
WHERE year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Net yield
- **French name:** Rendement net (yield)
- **Definition:** Net revenue earned per passenger-kilometre, expressed in euro cents. It measures how well each kilometre flown is paid, independently of the length of the route.
- **Définition (FR):** Chiffre d'affaires net par passager-kilomètre, en centimes d'euro. Il mesure la rémunération de chaque kilomètre parcouru.
- **Formula:** `100 * sum(net_fare_eur) / sum(distance_km)` over non-cancelled tickets, where `distance_km` comes from the ticket's route.
- **Unit:** euro cents per passenger-km
- **Shown in:** Route & Cabin Revenue
- **Pitfalls:** It uses the route distance of each ticket (an approximation of passenger-kilometres). Short-haul yield is naturally higher than long-haul yield, so never rank a short route against a long route; compare within the same haul.

```sql
SELECT r.haul,
       round(100 * sum(b.net_fare_eur) / sum(r.distance_km), 1) AS net_yield_cents_per_pkm
FROM bookings b
JOIN routes r USING (route_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Premium cabin share
- **French name:** Part des cabines premium
- **Definition:** Share of tickets sold in Premium Economy or Business, among all non-cancelled tickets.
- **Définition (FR):** Part des billets vendus en Premium Economy ou Business parmi les billets non annulés.
- **Formula:** `avg((cabin IN ('Premium Economy', 'Business'))::INT)` where `status <> 'cancelled'`.
- **Unit:** percent of tickets
- **Shown in:** Route & Cabin Revenue
- **Pitfalls:** It is a share of tickets, not of revenue. Short-haul routes have no Premium Economy cabin, so their premium share is Business only.

```sql
SELECT r.haul,
       round(100 * avg((b.cabin IN ('Premium Economy', 'Business'))::INT), 1) AS premium_cabin_share_pct
FROM bookings b
JOIN routes r USING (route_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 2 DESC;
```

### Average lead time
- **French name:** Délai d'achat moyen
- **Definition:** Average number of days between the booking date and the travel date, over non-cancelled tickets. It shows how far in advance travellers book.
- **Définition (FR):** Nombre moyen de jours entre la date de réservation et la date de voyage, sur les billets non annulés.
- **Formula:** `avg(date_diff('day', booking_date, travel_date))` where `status <> 'cancelled'`.
- **Unit:** days
- **Shown in:** Route & Cabin Revenue
- **Pitfalls:** Filtered on booking date, so recent months only contain trips booked so far.

```sql
SELECT r.haul,
       round(avg(date_diff('day', b.booking_date, b.travel_date)), 1) AS average_lead_time_days
FROM bookings b
JOIN routes r USING (route_id)
WHERE b.status <> 'cancelled'
  AND year(b.booking_date) = 2025
GROUP BY 1
ORDER BY 1;
```

### Target attainment
- **French name:** Taux d'atteinte de l'objectif
- **Definition:** Booked net revenue of a sales region in a quarter divided by the revenue target of that region for that quarter. 100% or more means the target was met.
- **Définition (FR):** Chiffre d'affaires net réservé d'une région commerciale sur un trimestre, divisé par l'objectif de cette région pour ce trimestre.
- **Formula:** `booked net revenue / target_revenue_eur`, per `sales_region` and `quarter`. The quarter label is `YYYY-Qn` and is based on `booking_date`.
- **Unit:** percent
- **Shown in:** Targets & Contract Compliance
- **Pitfalls:** The region is the account's **sales region** (where the account is headquartered), not the market region of the route. Targets exist only per region and quarter: there is no target per account, route or month.

```sql
WITH actual AS (
    SELECT a.sales_region,
           year(b.booking_date)::VARCHAR || '-Q' || quarter(b.booking_date)::VARCHAR AS quarter,
           sum(b.net_fare_eur) AS booked_net_revenue_eur
    FROM bookings b
    JOIN accounts a USING (account_id)
    WHERE b.status <> 'cancelled'
    GROUP BY 1, 2
)
SELECT t.sales_region, t.quarter,
       round(100 * a.booked_net_revenue_eur / t.target_revenue_eur, 1) AS target_attainment_pct
FROM targets t
JOIN actual a USING (sales_region, quarter)
ORDER BY t.quarter, t.sales_region;
```

### Commitment attainment
- **French name:** Taux de respect de l'engagement contractuel
- **Definition:** Tickets sold by an account in a period divided by the number of tickets it committed to buy over that period. The yearly commitment is scaled to the length of the period.
- **Définition (FR):** Billets vendus par un compte sur une période, divisés par l'engagement contractuel de billets proratisé sur la durée de la période.
- **Formula:** `tickets sold in the period / (annual_ticket_commitment * days_in_period / 365)`.
- **Unit:** percent
- **Shown in:** Targets & Contract Compliance
- **Pitfalls:** For a full calendar year the factor is 1. The year 2026 is incomplete (data stops on 2026-09-30, which is 273 days), so its commitment is prorated to 273/365. The proration is linear and ignores seasonality (August is always weak). Only non-cancelled tickets count.

```sql
WITH period AS (
    SELECT DATE '2026-01-01' AS p_start, DATE '2026-09-30' AS p_end
),
sold AS (
    SELECT b.account_id, count(*) AS tickets_sold
    FROM bookings b, period p
    WHERE b.status <> 'cancelled'
      AND b.booking_date BETWEEN p.p_start AND p.p_end
    GROUP BY 1
)
SELECT c.account_id,
       s.tickets_sold,
       round(c.annual_ticket_commitment * (date_diff('day', p.p_start, p.p_end) + 1) / 365.0) AS prorated_commitment,
       round(100 * s.tickets_sold / (c.annual_ticket_commitment * (date_diff('day', p.p_start, p.p_end) + 1) / 365.0), 1) AS commitment_attainment_pct
FROM contracts c
JOIN sold s USING (account_id), period p
ORDER BY commitment_attainment_pct ASC
LIMIT 10;
```

### Contract compliance status
- **French name:** Statut de conformité contractuelle
- **Definition:** A label given to each account from its Commitment attainment: **On track** at 100% or more, **At risk** from 85% up to (but not including) 100%, **Off track** below 85%.
- **Définition (FR):** Étiquette attribuée à chaque compte selon son taux de respect de l'engagement : « On track » à partir de 100 %, « At risk » de 85 % à moins de 100 %, « Off track » sous 85 %.
- **Formula:** `CASE WHEN attainment >= 1 THEN 'On track' WHEN attainment >= 0.85 THEN 'At risk' ELSE 'Off track' END`
- **Unit:** status label
- **Shown in:** Targets & Contract Compliance
- **Pitfalls:** The thresholds (100% and 85%) are the business rule for contracts. They are different from the colour bands used for Target attainment on the same dashboard.

```sql
WITH sold AS (
    SELECT account_id, count(*) AS tickets_sold
    FROM bookings
    WHERE status <> 'cancelled' AND year(booking_date) = 2025
    GROUP BY 1
),
att AS (
    SELECT c.account_id, s.tickets_sold / c.annual_ticket_commitment AS attainment
    FROM contracts c
    JOIN sold s USING (account_id)
)
SELECT CASE WHEN attainment >= 1 THEN 'On track'
            WHEN attainment >= 0.85 THEN 'At risk'
            ELSE 'Off track' END AS compliance_status,
       count(*) AS accounts
FROM att
GROUP BY 1
ORDER BY 2 DESC;
```

### Year-over-year growth
- **French name:** Croissance annuelle (en glissement annuel)
- **Definition:** Change of booked net revenue compared with the same period one year earlier, in percent.
- **Définition (FR):** Variation du chiffre d'affaires net réservé par rapport à la même période un an plus tôt, en pourcentage.
- **Formula:** `(revenue in period / revenue in same period one year earlier - 1) * 100`.
- **Unit:** percent
- **Shown in:** Account Performance
- **Pitfalls:** Periods must have the same length. The data starts on 2025-01-01, so growth can only be computed for periods in 2026 (January to September 2026 versus January to September 2025). There is no growth figure for 2025. Never compare a partial year with a full year.

```sql
WITH rev AS (
    SELECT a.sales_region,
           sum(CASE WHEN year(b.booking_date) = 2026 THEN b.net_fare_eur END) AS rev_2026_ytd,
           sum(CASE WHEN year(b.booking_date) = 2025 AND month(b.booking_date) <= 9 THEN b.net_fare_eur END) AS rev_2025_same_period
    FROM bookings b
    JOIN accounts a USING (account_id)
    WHERE b.status <> 'cancelled'
    GROUP BY 1
)
SELECT sales_region,
       round(100 * (rev_2026_ytd / rev_2025_same_period - 1), 1) AS yoy_growth_pct
FROM rev
ORDER BY 2 DESC;
```

## Business terms

### Corporate account
A company that buys tickets from the airline under a corporate contract (table `accounts`). Each account has one contract, one size tier, one headquarters city and one account manager.
Français : compte corporate, entreprise cliente avec un contrat négocié.

### Sales region
The Corporate Sales team that owns an account, based on where the account is headquartered: Europe, Americas, Africa & Middle East or Asia-Pacific (column `accounts.sales_region`). Targets and access rights are defined by sales region.
Français : région commerciale.

### Market region
The region of the destination (or origin) airport of a route that is not a hub (column `routes.market_region`). It describes where passengers fly to, not who the customer is. A European account flying to New York belongs to the sales region Europe and the market region Americas. Do not confuse it with Sales region.
Français : région de marché.

### Haul
A distance band of the route: **short** (up to 1,500 km), **medium** (over 1,500 km up to 5,000 km) or **long** (over 5,000 km). Short-haul routes have Economy and Business cabins; medium and long routes also have Premium Economy.
Français : segment de distance (court, moyen, long-courrier).

### Account size tier
The size class of an account: Small, Mid, Large or Strategic (column `accounts.size_tier`). Larger tiers buy more tickets and negotiate higher discounts.
Français : taille du compte.

### Cabin
The travel class of a ticket: Economy, Premium Economy or Business.
Français : cabine.

### Booking status
The state of a ticket: `flown` (the trip took place), `upcoming` (the trip is after the as-of date 2026-09-30) or `cancelled` (the ticket was cancelled and generates no revenue).
Français : statut de la réservation.

### Booking date and travel date
The booking date is when the company bought the ticket. The travel date is when the passenger flies. Booked metrics use the booking date; Flown net revenue uses the travel date.
Français : date de réservation et date de voyage.

### Hub
An airport where the airline connects its flights. The airline has two: Paris-Charles de Gaulle (CDG) and Amsterdam-Schiphol (AMS). Every route starts or ends at a hub.
Français : plateforme de correspondance.

### Corporate contract
The agreement between the airline and an account (table `contracts`). It defines the discount applied to the gross fare (`discount_pct`) and the minimum number of tickets the account commits to buy per year (`annual_ticket_commitment`). All contracts cover 2025-01-01 to 2026-12-31.
Français : contrat corporate, avec remise et engagement de volume.

### Data as-of date
The last day covered by the data: 2026-09-30. Everything described as "year to date" in 2026 means from 2026-01-01 to this date.
Français : date d'arrêté des données.

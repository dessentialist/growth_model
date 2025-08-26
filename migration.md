# New Tables Based Inputs UI set up

Tab 1:Simulation Definitions Set Up
//add, edit, delete values for these lists// 

Market
Market 1
Market 2
..

Sectors
Sector 1
Sector 2
..

Products
Product 1
Product 2
..

Tab 2: Simulation Specs 

Runtime
Time steps
Sector-Product Mapping mode or Sector mode
Scenario Name
Load Scenario
Scenario 
Reset To Baseline (where baseline is a 'special' scenario that is considered the baseline scenairo of the model)

Tab 3:
Primary Mapping 
//Sector-wise product selection //
//Mapping insights and summary//


Tab 4: Client Revenue

Client Revenue Stream (y axis to be sector_product values, dynamically filled in when combinations are added to the primary mapping)
Group	Comments	Parameter (per‑(s,m))
Market Activation	The total number of anchor clients for a material sector combination. 	ATAM
Market Activation	The year the market is activated for a particular sector material combination. 	anchor_start_year
Market Activation	The rate of generating leads per quarter for anchor clients for the sector material combination, where each sector material may draw from a common client name. We do not divide between particular clients, but only by client numbers. 	anchor_lead_generation_rate
Market Activation	A bracket conversion rate to show how many potential clients we believe we can get from a particular set of leads for the sector material combination. 	lead_to_pc_conversion_rate
Market Activation	The rate per quarter of generating projects from a potential client. 	project_generation_rate
Market Activation	The number of quarters that the average project lasts once started by a particular anchor client. 	project_duration
Market Activation	The number of projects it takes for a potential client to become a client that will then start placing commercial orders. 	projects_to_client_conversion
Market Activation	The maximum number of projects a potential client generates. This is meant only as a binary on-off switch for a sector material combination, since it is assumed that the project conversion number will be lower than the maximum projects. 	max_projects_per_pc
Market Activation	The number of quarters before which an active client starts placing a commercial order after it becomes an active client. 	anchor_client_activation_delay
Orders 	The number of quarters of the initial testing phase. 	initial_phase_duration
Orders 	The starting rate of kilograms ordered per quarter per client for each sector material combination. 	initial_requirement_rate
Orders 	Percentage growth of orders per quarter in the initial testing phase. 	initial_req_growth
Orders 	The number of quarters during which requirement may grow at a significant rate. 	ramp_phase_duration
Orders 	The starting rate of order of kgs per quarter for each sector material combination during the ramp-up phase. 	ramp_requirement_rate
Orders 	Percentage growth of rate of order per kg per material during the ramp-up phase. 	ramp_req_growth
Orders 	The starting rate of order of kilograms per material per quarter for each sector-material pair when the client enters a steady order phase that is assumed to grow in perpetuity. 	steady_requirement_rate
Orders 	The percentage rate of growth of orders per quarter in the steady state. 	steady_req_growth
Orders 	The number of quarters between receiving a requirement and fulfilling the delivery for that requirement. 	requirement_to_order_lag
Seeds	The total number of projects that are already completed for a material sector combination. 	completed_projects_sm
Seeds	The total number of active clients already present in the material sector combination at time T0. 	active_anchor_clients_sm
Seeds	The number of quarters that have elapsed since a client became active for the material sector combination at time T0. 	elapsed_quarters

Tab 4: Direct Market Revenue

Direct Market Revenue Stream (y axis to be sector_product values, dynamically filled in when combinations are added to the primary mapping)
Comments	Parameters
year the material begins receiving other-client leads	lead_start_year
per quarter inbound leads for the material	inbound_lead_generation_rate (per quarter)
per quarter outbound leads for the material	outbound_lead_generation_rate (per quarter)
lead to client conversion	lead_to_c_conversion_rate (fraction)
lead-to-requirement delay for first order by a lead	lead_to_requirement_delay (quarters)
requirement-to-delivery delay for running requirements	requirement_to_fulfilment_delay (quarters)
starting order quantity	avg_order_quantity_initial (units per client)
percentage growth of order quantity per quarter	client_requirement_growth (per quarter growth)
total addressable market for other clients	TAM (clients)

Tab 5: Lookup Points

Lookup Points Table (y-axis to be years)

Production Capacity in Units
Product 1
Product 2
.
.

Price Per Unit
Product 1
Product 2
.
.

Tab 6: Runner
//Scenario save, validate, and run controls//


Tab 7: Logs
//Simualation logs//
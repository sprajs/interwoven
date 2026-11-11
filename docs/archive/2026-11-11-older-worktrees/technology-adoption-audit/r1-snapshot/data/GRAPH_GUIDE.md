# Graph guide and edge inventory

The graph is a typed, directed multigraph. `depends-on` points from a dependent system to a bounded requirement; `enables` points from a contributor to a beneficiary. `complements` does not assert universal necessity. `displaces` is scoped to the listed task, population and period.

Node identities remain local to their contribution. Similar labels do not silently become identical technologies. No global invention ancestry or transitive causal closure is asserted. Multiple incoming edges do not by themselves establish joint requirements, alternatives or sufficient causes. Every edge carries an explicit basis, scope, alternatives, joint-input list, necessity rationale and dispute.

| Edge | From | Relation | To | Basis | Cases / claims |
|---|---|---|---|---|---|
| ANC-E01 | Hero's steam-driven rotating sphere as described | depends-on | Steam from a heated water vessel in Hero's configuration | bounded-necessity | ANC-C01 / ANC-K01 |
| ANC-E02 | Sphere, outlets and pivot assembly in Hero's description | enables | Hero's steam-driven rotating sphere as described | technical-possibility | ANC-C01 / ANC-K01; ANC-K03 |
| ANC-E03 | Barbegal watermill trains | depends-on | Aqueduct flow supplied to Barbegal | bounded-necessity | ANC-C02 / ANC-K04; ANC-K06 |
| ANC-E04 | Barbegal wooden component repair and adjustment | complements | Barbegal watermill trains | observed-contribution | ANC-C02 / ANC-K04; ANC-K06 |
| ANC-E05 | Seasonal flour demand near Arles (hypothesised market) | enables | Barbegal watermill trains | hypothesis | ANC-C02 / ANC-K05 |
| ANC-E06 | Rome's enslaved specialist maintenance workforce around 100 CE | complements | Rome's urban aqueduct service around 100 CE | observed-contribution | ANC-C03 / ANC-K08; ANC-K09 |
| ANC-E07 | Public treasury, imperial purse and water-right revenue at Rome | enables | Rome's enslaved specialist maintenance workforce around 100 CE | observed-contribution | ANC-C03 / ANC-K09 |
| ANC-E08 | Rome's aqueduct allocation and maintenance-access rights | complements | Rome's urban aqueduct service around 100 CE | observed-contribution | ANC-C03 / ANC-K09; ANC-K10 |
| ANC-E09 | Fodder scarcity during the 537 siege | constrains | Animal-driven grinding as a 537 alternative | observed-contribution | ANC-C03 / ANC-K11 |
| ANC-E10 | Tiber boatmills reported in the 537 siege | displaces | Rome's aqueduct-fed mills described for 537 | observed-contribution | ANC-C03 / ANC-K11 |
| ANC-E11 | Tiber boatmills reported in the 537 siege | depends-on | Tiber current at boatmill moorings | bounded-necessity | ANC-C03 / ANC-K11 |
| ANC-E12 | Rome's aqueduct-fed mills described for 537 | depends-on | Aqueduct flow to Rome's mills in the 537 account | bounded-necessity | ANC-C03 / ANC-K11 |
| ANC-E13 | Early southeast Arabian groundwater galleries | depends-on | Groundwater at an elevation compatible with gallery outlet | bounded-necessity | ANC-C04 / ANC-K15 |
| ANC-E14 | Deepening and clearing at al-Madam | complements | Early southeast Arabian groundwater galleries | observed-contribution | ANC-C04 / ANC-K13 |
| ANC-E15 | Multigenerational cultivation rights reported by Polybius | enables | Northern Iranian channels in Polybius's narrative | hypothesis | ANC-C04 / ANC-K14 |
| ANC-E16 | Late Han Dujiangyan water officials and labour organisation | enables | Late Han Dujiangyan repair activity | observed-contribution | ANC-C05 / ANC-K16; ANC-K17 |
| ANC-E17 | Late Han Dujiangyan repair activity | complements | Dujiangyan diversion works attested by late Han repair evidence | observed-contribution | ANC-C05 / ANC-K16 |
| ANC-E18 | Geometry and flow regimes specified in the 2020 Dujiangyan model | enables | Dujiangyan headworks in the 2020 numerical experiment | technical-possibility | ANC-C05 / ANC-K18 |
| ANC-E19 | Dredging to the profile discussed in the modern Dujiangyan study | complements | Dujiangyan headworks in the 2020 numerical experiment | technical-possibility | ANC-C05 / ANC-K18 |
| ANC-E20 | Dholavira runoff-fed storage and diversion works | depends-on | Seasonal runoff captured by Dholavira storage | bounded-necessity | ANC-C06 / ANC-K19 |
| ANC-E21 | Repair of Dholavira water structures | complements | Dholavira runoff-fed storage and diversion works | hypothesis | ANC-C06 / ANC-K19; ANC-K21 |
| DIG-E01 | Heterogeneous remote computing/network access at CERN, 1989 | enables | CERN distributed hypertext design, 1989 | technical-possibility | DIG-C01 / DIG-K01 |
| DIG-E02 | Existing CERN information accessible through links, 1989 design | complements | CERN distributed hypertext design, 1989 | technical-possibility | DIG-C01 / DIG-K01 |
| DIG-E03 | CERN reuse permissions for released Web code, 1993–1994 | enables | External reuse of CERN client/server/library code, 1993–1994 | technical-possibility | DIG-C01 / DIG-K02 |
| DIG-E04 | US household desktop/laptop access, 2015 ACS | complements | US household handheld-computer access, 2015 ACS | hypothesis | DIG-C02 / DIG-K04; DIG-K25 |
| DIG-E05 | UK smartphone internet access, 2015 | competes-with | UK laptop internet access, 2015 | technical-possibility | DIG-C03 / DIG-K05; DIG-K24 |
| DIG-E06 | UK household tablet internet alternative, 2015 | competes-with | UK smartphone internet access, 2015 | technical-possibility | DIG-C03 / DIG-K06; DIG-K24 |
| DIG-E07 | Recurring service affordability for US dependent users, 2014 | constrains | US smartphone-dependent internet access, 2014 | observed-contribution | DIG-C03 / DIG-K08; DIG-K24 |
| DIG-E08 | UK laptop/desktop forms/documents comparator, 2023 | competes-with | UK smartphone forms/documents, 2023 | technical-possibility | DIG-C03 / DIG-K09; DIG-K24 |
| DIG-E09 | Shared smartphone presence in rural Indian homes, 2021 | enables | Study through household smartphones in rural India, 2021 | technical-possibility | DIG-C04 / DIG-K12; DIG-K13 |
| DIG-E10 | Child control of available household smartphone for study, 2021 | constrains | Study through household smartphones in rural India, 2021 | observed-contribution | DIG-C04 / DIG-K13 |
| DIG-E11 | SMS-capable phones used in early Kenyan M-PESA | enables | Early Kenyan M-PESA account transfers, 2007–2010 | technical-possibility | DIG-C05 / DIG-K14 |
| DIG-E12 | Working carrier network for early Kenyan M-PESA | complements | Early Kenyan M-PESA account transfers, 2007–2010 | observed-contribution | DIG-C05 / DIG-K14; DIG-K15 |
| DIG-E13 | Immediate cash redemption at a particular M-PESA agent, 2008–2009 | depends-on | Sufficient cash at that M-PESA agent, 2008–2009 | bounded-necessity | DIG-C05 / DIG-K14; DIG-K15 |
| DIG-E14 | Early M-PESA customer registration and ID checks | complements | Early Kenyan M-PESA account transfers, 2007–2010 | observed-contribution | DIG-C05 / DIG-K14; DIG-K17 |
| DIG-E15 | Bank-held M-PESA funds and agent banking links, early implementation | complements | Early Kenyan M-PESA account transfers, 2007–2010 | observed-contribution | DIG-C05 / DIG-K14 |
| DIG-E16 | UK VR-headset gaming, 2023 | competes-with | UK phone/smartphone gaming, 2023 | technical-possibility | DIG-C06 / DIG-K18; DIG-K21 |
| DIG-E17 | Wearing/interface demands of tested Quest 2 work setup | constrains | Tested Quest 2 virtual desktop work configuration, 2022 study | observed-contribution | DIG-C06 / DIG-K19 |
| DIG-E18 | Matched physical desktop work comparator, 2022 study | competes-with | Tested Quest 2 virtual desktop work configuration, 2022 study | technical-possibility | DIG-C06 / DIG-K19 |
| DIG-E19 | Shared compatible applications/developer participation in Microsoft strategy, 2015 | complements | Microsoft Lumia phone business, FY 2015 | hypothesis | DIG-C07 / DIG-K23 |
| DIG-E20 | Phone distributor/carrier participation proposed for Microsoft comparison, 2015 | enables | Microsoft Lumia phone business, FY 2015 | hypothesis | DIG-C07 / DIG-K23 |
| IND-E01 | Dependable accessible waterpower | enables | Mine water pumping | technical-possibility | IND-C01 / IND-K01; IND-K02 |
| IND-E02 | Remote rod transmission and maintainable components | complements | Mine water pumping | technical-possibility | IND-C01 / IND-K01; IND-K02 |
| IND-E03 | Human and animal hauling | enables | Mine water pumping | technical-possibility | IND-C01 / IND-K01 |
| IND-E04 | Low delivered coal cost at an early mine site | enables | Fuel-intensive atmospheric steam engine | observed-contribution | IND-C02 / IND-K03 |
| IND-E05 | Fuel-efficient Cornish pumping engines | competes-with | Fuel-intensive atmospheric steam engine | observed-contribution | IND-C02 / IND-K03 |
| IND-E06 | Comparative engine reporting | complements | Fuel-efficient Cornish pumping engines | observed-contribution | IND-C02 / IND-K04 |
| IND-E07 | Cost-book investment and overlapping mine ownership | enables | Comparative engine reporting | observed-contribution | IND-C02 / IND-K04 |
| IND-E08 | Watt patent and royalty regime | constrains | Fuel-efficient Cornish pumping engines | hypothesis | IND-C02 / IND-K05 |
| IND-E09 | Steam in British textile mills | competes-with | Dependable accessible waterpower | observed-contribution | IND-C03 / IND-K07; IND-K08 |
| IND-E10 | Steam in British textile mills | complements | Dependable accessible waterpower | observed-contribution | IND-C03 / IND-K07 |
| IND-E11 | Collective reservoir schemes | enables | Dependable accessible waterpower | hypothesis | IND-C03 / IND-K08 |
| IND-E12 | Collective reservoir schemes | complements | Collective financing and water-use coordination | hypothesis | IND-C03 / IND-K08 |
| IND-E13 | Precision skills, gauges and machine tools | complements | Mechanised British spinning | observed-contribution | IND-C04 / IND-K12 |
| IND-E14 | Cheap and controlled labour recruitment | complements | Mechanised British spinning | observed-contribution | IND-C04 / IND-K10; IND-K11 |
| IND-E15 | Mechanised British spinning | enables | Indian and Lancashire cotton-market competition | observed-contribution | IND-C05 / IND-K13 |
| IND-E16 | Raw cotton supply and delivery costs | constrains | Indian and Lancashire cotton-market competition | observed-contribution | IND-C05 / IND-K13 |
| IND-E17 | Colonial tariff authority and Atlantic market formation | constrains | Indian and Lancashire cotton-market competition | observed-contribution | IND-C05 / IND-K15; IND-K16 |
| IND-E18 | Imported cotton mixtures and preparation work | complements | Japanese ring-spinning package | observed-contribution | IND-C06 / IND-K17 |
| IND-E19 | Japanese ring-spinning package | competes-with | Mule spinning and specific operative skills | observed-contribution | IND-C06 / IND-K17; IND-K18 |
| IND-E20 | High-draft fibre control | displaces | Mule spinning and specific operative skills | observed-contribution | IND-C06 / IND-K19; IND-K18 |
| IND-E21 | High-draft fibre control | complements | Japanese ring-spinning package | observed-contribution | IND-C06 / IND-K19 |
| IND-E22 | Factory-spun cotton yarn | complements | Chinese handloom weaving | observed-contribution | IND-C07 / IND-K20 |
| IND-E23 | Factory-spun cotton yarn | displaces | Chinese hand spinning | observed-contribution | IND-C07 / IND-K20; IND-K21 |
| IND-E24 | Chinese hand spinning | complements | Chinese handloom weaving | observed-contribution | IND-C07 / IND-K20 |
| IND-E25 | Household allocation and gender norms | complements | Chinese handloom weaving | hypothesis | IND-C07 / IND-K22 |
| IND-E26 | Electric unit drive | competes-with | Electric line-shaft or group drive | observed-contribution | IND-C08 / IND-K23; IND-K24 |
| IND-E27 | Compatible machines and reorganised production | complements | Electric unit drive | observed-contribution | IND-C08 / IND-K24 |
| IND-E28 | Utilities and application services | enables | Electric unit drive | observed-contribution | IND-C08 / IND-K24 |
| IND-E29 | Existing onsite generation and shafts | constrains | Electric unit drive | observed-contribution | IND-C08 / IND-K24 |
| IND-E30 | Electric line-shaft or group drive | complements | Existing onsite generation and shafts | observed-contribution | IND-C08 / IND-K23 |
| LBR-E01 | Adapted telephone service organisation | complements | Mechanical local telephone switching | observed-contribution | LBR-C01 / LBR-K01 |
| LBR-E02 | Mechanical local telephone switching | displaces | Manual local telephone switching | observed-contribution | LBR-C01 / LBR-K02 |
| MAT-E01 | Forager ceramic vessels | complements | Aquatic-food cooking practices | observed-contribution | MAT-C01 / MAT-K03 |
| MAT-E02 | Bronze working in southern Levant | complements | Systematic southern Levant iron production | hypothesis | MAT-C02 / MAT-K07 |
| MAT-E03 | Systematic southern Levant iron production | competes-with | Bronze working in southern Levant | observed-contribution | MAT-C02 / MAT-K04 |
| MAT-E04 | Local administrative support (hypothesis) | enables | Systematic southern Levant iron production | hypothesis | MAT-C02 / MAT-K07 |
| MAT-E05 | Systematic southern Levant iron production | depends-on | Iron-bearing ore for surveyed southern Levant primary smelting | bounded-necessity | MAT-C02 / MAT-K07 |
| MAT-E06 | Later/post-Meroitic bloomery process and its modern replica | depends-on | Suitable iron-bearing ore charge in Meroe replica smelts | bounded-necessity | MAT-C04 / MAT-K12 |
| MAT-E07 | Later/post-Meroitic bloomery process and its modern replica | complements | Bellows, tuyères and coordinated operation at Meroe | observed-contribution | MAT-C04 / MAT-K12 |
| MAT-E08 | Selected Acacia charcoal at Meroe | enables | Later/post-Meroitic bloomery process and its modern replica | observed-contribution | MAT-C04 / MAT-K13 |
| MAT-E09 | Early Chinese practical cast-iron implements | complements | Early Chinese casting mould expertise | hypothesis | MAT-C03 / MAT-K09 |
| MAT-E10 | Annealing early Chinese cast-iron implements | enables | Early Chinese practical cast-iron implements | technical-possibility | MAT-C03 / MAT-K09 |
| MAT-E11 | Annealing early Chinese cast-iron implements | complements | Charcoal for early Chinese cast-iron heat treatment | technical-possibility | MAT-C03 / MAT-K09 |
| MAT-E12 | Mineral fuel in Song–Yuan iron manufacture | competes-with | Charcoal in Song–Yuan iron manufacture | observed-contribution | MAT-C03 / MAT-K10 |
| MAT-E13 | Andean arsenical bronze | complements | Thin-sheet fabrication | technical-possibility | MAT-C05 / MAT-K15 |
| MAT-E14 | Andean tin bronze | competes-with | Andean arsenical bronze | observed-contribution | MAT-C05 / MAT-K17 |
| MAT-E15 | Peruvian oxide/sulpharsenide cosmelting | enables | Andean arsenical bronze | technical-possibility | MAT-C05 / MAT-K16 |
| MAT-E16 | Sound, colour and ritual demand | complements | West Mexican bells and ornaments | hypothesis | MAT-C06 / MAT-K18 |
| MAT-E17 | Ile-Ife primary glassmaking | complements | Refractory crucibles | observed-contribution | MAT-C07 / MAT-K21 |
| MAT-E18 | Locally compatible feldspar-rich raw batch | enables | Ile-Ife primary glassmaking | observed-contribution | MAT-C07 / MAT-K20; MAT-K22 |
| MAT-E19 | Imported glass objects | competes-with | Ile-Ife primary glassmaking | hypothesis | MAT-C07 / MAT-K20 |
| MOB-E01 | Roman road freight in modeled networks and lowland Britain | complements | Roman river and maritime freight in the same scoped comparisons | technical-possibility | MOB-C01 / MOB-K01; MOB-K03 |
| MOB-E02 | Roman road freight in modeled networks and lowland Britain | competes-with | Roman river and maritime freight in the same scoped comparisons | technical-possibility | MOB-C01 / MOB-K02; MOB-K03 |
| MOB-E03 | Roman freight access, handling, storage and transfer tasks | constrains | Roman river and maritime freight in the same scoped comparisons | technical-possibility | MOB-C01 / MOB-K03 |
| MOB-E04 | Seasonal winds, storms and route conditions in ORBIS v1 | constrains | Roman river and maritime freight in the same scoped comparisons | technical-possibility | MOB-C01 / MOB-K01 |
| MOB-E05 | Inka wayside stores, shelter and road engineering | complements | Inka roads and the surveyed Atacama segment | observed-contribution | MOB-C02 / MOB-K04 |
| MOB-E06 | Water and forage availability at Cachiyuyo de Llampos | constrains | Inka roads and the surveyed Atacama segment | hypothesis | MOB-C02 / MOB-K05 |
| MOB-E07 | Inka roads and the surveyed Atacama segment | enables | Local mining-craft production and roadside exchange at Cachiyuyo | observed-contribution | MOB-C02 / MOB-K06 |
| MOB-E08 | Early Indian railway guaranteed concessions | enables | Colonial Indian railway network | observed-contribution | MOB-C03 / MOB-K07 |
| MOB-E09 | Colonial Indian route planning and military priorities | enables | Colonial Indian railway network | observed-contribution | MOB-C03 / MOB-K07 |
| MOB-E10 | Colonial Indian railway network | enables | Indian district agricultural market integration | observed-contribution | MOB-C03 / MOB-K08 |
| MOB-E11 | Contractual state purchases and treasury incentives in Indian railways | constrains | Indian railway employment and operating organization | observed-contribution | MOB-C03 / MOB-K09 |
| MOB-E12 | Ghana western and eastern railway services | enables | Ghana cocoa cultivation and commercial shipment | observed-contribution | MOB-C04 / MOB-K12 |
| MOB-E13 | Ghana western and eastern railway services | enables | Settlement concentration near Ghana railway routes | observed-contribution | MOB-C04 / MOB-K12; MOB-K13 |
| MOB-E14 | Ghana railway repair and operating-finance arrangements | complements | Ghana western and eastern railway services | observed-contribution | MOB-C04 / MOB-K14 |
| MOB-E15 | Ghana post-independence road services | displaces | Ghana western and eastern railway services | observed-contribution | MOB-C04 / MOB-K13 |
| MOB-E16 | Settlement concentration near Ghana railway routes | enables | Later co-location of population and investment in Ghana | hypothesis | MOB-C04 / MOB-K13 |
| MOB-E17 | Specialist fleet operation and battery maintenance | complements | EVC managed electric-cab services, 1897–1907 | observed-contribution | MOB-C05 / MOB-K15 |
| MOB-E18 | Lead-acid battery condition under particular duty cycles | constrains | EVC managed electric-cab services, 1897–1907 | observed-contribution | MOB-C05 / MOB-K16; MOB-K17 |
| MOB-E19 | Specialist fleet operation and battery maintenance | complements | US electric commercial fleet applications after 1909 | observed-contribution | MOB-C05 / MOB-K17 |
| MOB-E20 | EVAA utility coordination and proposed charging standards, 1909–1916 | complements | US electric commercial fleet applications after 1909 | observed-contribution | MOB-C05 / MOB-K18 |
| MOB-E21 | Early US privately operated gasoline cars | displaces | Early US privately operated electric passenger cars | observed-contribution | MOB-C05 / MOB-K17 |
| MOB-E22 | US/ISO container dimension and handling standards | complements | Postwar intermodal container transport | observed-contribution | MOB-C06 / MOB-K19; MOB-K20 |
| MOB-E23 | Compatible cranes, terminals, ships and inland facilities | complements | Postwar intermodal container transport | observed-contribution | MOB-C06 / MOB-K19 |
| MOB-E24 | US military container logistics demand in Vietnam | enables | Postwar intermodal container transport | observed-contribution | MOB-C06 / MOB-K20 |
| MOB-E25 | West Coast mechanization bargain and compensation fund | enables | Postwar intermodal container transport | observed-contribution | MOB-C06 / MOB-K22 |
| MOB-E26 | Postwar intermodal container transport | displaces | Traditional repeated break-bulk dock-handling tasks | observed-contribution | MOB-C06 / MOB-K23 |
| MOB-E27 | Postwar intermodal container transport | enables | Off-dock container stuffing and unstuffing | observed-contribution | MOB-C06 / MOB-K23 |
| MOB-E28 | Singapore state port planning and waterfront allocation | enables | Singapore Tanjong Pagar/Pasir Panjang container terminals | observed-contribution | MOB-C07 / MOB-K24 |
| MOB-E29 | Singapore terminal workforce and information-service development | complements | Singapore Tanjong Pagar/Pasir Panjang container terminals | observed-contribution | MOB-C07 / MOB-K24 |

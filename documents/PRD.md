# HR Management System, Showcase and Production PRD

Nov 27, 2026 · @Rachit Singh

This file holds two separate documents. Part 1 is the showcase PRD for the restaurant demo, and Part 2 is the production PRD to use once a buyer commits. Build from Part 1 now and open Part 2 only after the restaurant meeting. Anything Part 1 leaves out is not forgotten, it is planned in Part 2.

## Part 1. Showcase PRD for the Restaurant Demo

The showcase is a small but working version of the product, built to win one meeting with the restaurant owner and to show us what he would pay for. It runs on realistic sample data and tells one complete story, from staff records to a shift on the floor to a performance view.

### Purpose

The showcase has worked if three things happen. The owner sees his own business in it within the first two minutes. He can name the one problem he would pay to fix first. He agrees to a follow-up that leads toward a paid pilot.

The build estimate is 3 to 4 weeks for one developer and one designer. Confirm this with whoever builds it before promising a date.

### The problem in a restaurant

Most restaurant owners keep staff details in a phone contact list and a notebook. The weekly rota goes out in a chat group and changes get lost in the scroll. Lateness is noticed only when a shift is already short. Turnover is high, so records go stale quickly, and an owner with more than one branch cannot compare branches without phoning each manager.

The showcase targets four pain points.

- Staff details are scattered across phones and paper.
- Shift changes are lost in chat.
- Nobody keeps a record of who arrived late.
- The owner has no view of how people or branches are performing.

### Users and roles

| Role | What they do in the showcase |
| --- | --- |
| Owner | Sees every branch, the full staff directory and the performance dashboard |
| Branch manager | Builds the weekly shift plan, assigns targets and watches attendance for one branch |
| Shift supervisor | Marks attendance and sees today's shift |
| Staff member | Sees own profile, shifts and targets, and clocks in and out from a phone |

### Showcase features

Every must-have item is needed for the demo story to hold together. Nice-to-have items go in only if time remains, and none of them should delay the meeting.

| Area | Feature | Priority |
| --- | --- | --- |
| People | Staff directory and profiles with name, auto-generated employee ID, role, branch, phone, address, emergency contact, start date and photo | Must-have |
| People | Two sample branches, with the owner able to see both | Must-have |
| Access | Four roles with different screens, enforced on the server | Must-have |
| Access | Staff login by phone number and one-time code, with the code simulated in the demo | Must-have |
| Shifts | Weekly shift grid where a manager assigns staff, with a copy-last-week button | Must-have |
| Shifts | Staff view of their own upcoming shifts on a phone | Must-have |
| Attendance | Clock in and clock out from a phone, with late arrivals flagged against shift start | Must-have |
| Attendance | Attendance record per person per day showing on time, late or absent | Must-have |
| Performance | A fixed starter set of restaurant KPIs such as on-time attendance, customer rating, upsell rate and food waste | Must-have |
| Performance | Manager assigns a numeric target for a KPI to a staff member, with progress shown against it | Must-have |
| Dashboards | Owner dashboard with headcount by branch, attendance rate, late arrivals this week and KPI status per branch | Must-have |
| Dashboards | Staff dashboard with own attendance and targets | Must-have |
| Data | Sample data with 25 staff, two branches and four weeks of attendance and KPI history | Must-have |
| Polish | Restaurant name and logo shown across the app | Nice-to-have |
| Shifts | Shift swap request between two staff members | Nice-to-have |
| People | CSV import of the real staff list | Nice-to-have |
| Performance | Manager comments on a target | Nice-to-have |
| Alerts | Real SMS or WhatsApp message for new shifts | Nice-to-have |

The logo item is cheap and tends to change how an owner reacts, so build it early if there is any slack.

### Demo flow

The demo should run in about eight minutes, on a laptop for the owner views and on a phone for the staff views.

1. Open as the owner. Show the staff directory across both branches, search for a name and open a profile.
2. Switch to a branch manager and build next week's shifts on the weekly grid.
3. Switch to a staff member on the phone, log in with a phone number, view the shifts and clock in.
4. Show the late arrival being flagged automatically.
5. Back as the manager, assign a target to that staff member, such as 95 percent on-time attendance.
6. Back as the owner, open the dashboard and compare the two branches on attendance and KPI status.
7. Ask the meeting questions below.

### Questions to ask the owner

- Which of these problems would you pay to fix first?
- How many branches and staff do you have, and how do you plan shifts today?
- Do your staff have work email, or is a phone number the only way to reach them?
- What do you pay now for any scheduling or HR tool?
- What monthly price would feel fair to you?

### Success criteria for the showcase

- The owner names one problem he would pay to fix first.
- He asks for access, a trial or a follow-up date before the meeting ends.
- He shares real data, such as a staff list or this week's rota.
- The demo runs without crashes or manual fixes behind the scenes.
- We leave knowing his price range.

### What the showcase does not include

- Payroll, tips and leave balances.
- Hiring and onboarding checklists.
- Signup, billing and multiple companies.
- Real email or SMS delivery.
- A custom KPI builder or weighted scoring.
- Other sectors and the sector selector.
- Backups, audit log and security testing. Permissions are still enforced.
- A native mobile app.

### Foundation rules the showcase must follow

These are small to build now and expensive to fix later, so they hold even in a demo.

1. Every record carries a company ID. Only one company exists today.
2. Job titles, branches and KPIs are stored as editable data and never typed into the code.
3. Permissions are checked on the server, and not only hidden on the screen.
4. Shift and clock-in features sit in their own module, apart from the core employee records.
5. Employee records are deactivated and never deleted.
6. The demo uses a real database and real login code from day one, with no shortcuts that must be torn out later.

## Part 2. Production PRD

Use this part once the restaurant owner or another buyer commits. It turns the showcase into a product that several companies can safely pay for, using the same foundation, hardened, extended and made configurable.

### Vision

A multi-company HR and performance platform where each customer gets its own private workspace, set up from a sector template so it is useful within minutes. Restaurants come first because a real buyer already exists. Other sectors follow as templates on the same core.

### Customers and sector order

| Sector | Core need | Extra work beyond the core | Release |
| --- | --- | --- | --- |
| Restaurants and cafes | Shifts, attendance, mobile access for hourly staff, branch comparison | Shift and attendance module, phone login | First release |
| Marketing agencies | KPI and utilization targets for desk-based teams | Template only | After two paying restaurants |
| Real estate agencies | Listing, viewing and commission targets | Template only | After two paying restaurants |
| Health clinics | Staff records plus license and credential tracking | Credential module, stricter privacy controls, compliance review | Only if demand is proven |

### Problem

Small and mid-sized companies run people operations on chat groups and spreadsheets. Records go stale, targets are vague and employees cannot see where they stand between reviews. Owners with several locations have no clean way to compare them. Enterprise HR suites solve this but cost too much, take too long to set up and ship modules these companies will never use.

### Users and roles

| Role | Access |
| --- | --- |
| Platform super admin | Our own team. Manages customer accounts, plans and support. Sees no personal employee data unless a customer grants access, and every grant is logged |
| Company owner | Full access inside their company, including billing and all locations |
| HR admin | People records, organization setup, KPI library and reports |
| Branch or team manager | Records, shifts, targets and dashboards for their own team only |
| Shift supervisor | Attendance and the current shift, used in the restaurant template |
| Employee | Own profile, shifts, targets and performance |

### Goals for the production release

1. A new company signs up, picks a sector and has its first 50 staff live within one working day.
2. One company can never see another company's data.
3. Owners and managers see attendance and performance without building a report by hand.
4. A new sector can be added mostly by writing a template, with little new code.

### Production features

Must-have means the product cannot be sold without it. Nice-to-have means it improves the experience and can follow in a later release.

| Area | Feature | Priority |
| --- | --- | --- |
| Accounts | Private workspace per company with isolated data | Must-have |
| Accounts | Self-serve signup, email verification and a free trial | Must-have |
| Accounts | Login by email, or by phone number with a one-time code for staff without email | Must-have |
| Accounts | Single sign-on with Google or Microsoft | Nice-to-have |
| Accounts | Two-factor authentication | Nice-to-have |
| Accounts | Custom roles with granular permissions | Nice-to-have |
| Organization | Locations, departments, job titles and one direct manager per employee | Must-have |
| Organization | Org chart view | Nice-to-have |
| People | Create, edit and deactivate employee records with automatic IDs in a configurable format | Must-have |
| People | Profiles with contact details, emergency contact and photo, where employees edit only a limited set of fields | Must-have |
| People | Field-level visibility by role | Must-have |
| People | Searchable directory with filters and sorting | Must-have |
| People | CSV import with preview and row-level errors, plus CSV export | Must-have |
| People | Duplicate detection on phone, email and employee ID | Must-have |
| People | Custom fields on the employee record | Nice-to-have |
| People | Document attachments such as signed contracts | Nice-to-have |
| People | Field-by-field change history | Nice-to-have |
| Shifts and attendance | Weekly shift scheduling with shift templates, branch opening hours and copy-last-week | Must-have |
| Shifts and attendance | Clock in and out from a phone with late flags | Must-have |
| Shifts and attendance | Attendance records and reports per person, branch and period | Must-have |
| Shifts and attendance | Shift swap requests with manager approval | Must-have |
| Shifts and attendance | Clock-in restricted to the branch location | Nice-to-have |
| KPIs and targets | KPI library with unit, direction and measurement frequency | Must-have |
| KPIs and targets | Targets for individuals and teams with start and end dates | Must-have |
| KPIs and targets | Weighting and an overall score | Must-have |
| KPIs and targets | Progress entry by hand or CSV, with status calculated as on track, at risk or off track | Must-have |
| KPIs and targets | Review periods that lock when closed | Must-have |
| KPIs and targets | Starter KPI sets by role and sector | Must-have |
| KPIs and targets | Cascading goals from company to team to person | Nice-to-have |
| KPIs and targets | Employee acknowledgment of a target | Nice-to-have |
| KPIs and targets | Self-assessment and manager comments per period | Nice-to-have |
| Dashboards | Employee, manager and company dashboards limited by role | Must-have |
| Dashboards | Branch and team comparison | Must-have |
| Dashboards | CSV export of any dashboard table | Must-have |
| Dashboards | PDF performance summary per employee | Nice-to-have |
| Dashboards | Heatmaps and configurable widgets | Nice-to-have |
| Notifications | Email for new or changed targets and overdue updates | Must-have |
| Notifications | SMS or WhatsApp for staff without email, used in the restaurant template | Must-have |
| Notifications | Weekly digest for managers | Nice-to-have |
| Notifications | Slack or Microsoft Teams alerts | Nice-to-have |
| Administration | Configurable ID format, review periods and basic branding | Must-have |
| Administration | Audit log of changes and views of sensitive fields | Must-have |
| Administration | Full data export for the customer | Must-have |

### SaaS platform requirements

These are the parts that turn one working app into a product many companies can buy.

**Must-have**

- Every database query is scoped by company ID, with automated tests that prove one company cannot read another's data.
- Monthly subscription billing with invoices, a free trial and handling for failed payments.
- A super admin console to list companies, see plan and status, suspend an account and open a logged support session.
- An onboarding wizard that asks for the sector, loads its template and imports the first staff list.
- Usage tracking per company, covering employees, locations and logins.
- Data export and deletion when a customer leaves.

**Nice-to-have**

- Annual billing and discount codes.
- In-app help and a guided tour.
- A customer health score based on usage.

### Plans and pricing

Prices are not set yet and should come from the owner conversations. The structure below is the starting assumption.

| Plan | Who it suits | Price basis | Includes |
| --- | --- | --- | --- |
| Basic | Single restaurant or small team | Flat monthly fee per location | Staff records, profiles, shifts and attendance |
| Pro | Multi-branch owners and office teams | Flat fee per location in restaurants, per employee in office sectors | Everything in Basic plus KPIs, targets, dashboards and branch comparison |

Restaurants are priced per location because their headcount swings with turnover and seasons. Office sectors are priced per employee because headcount there is steady.

### Sector templates

A template is a bundle of defaults loaded when a company picks its sector. It sets job titles, departments, starter KPIs, the review period, the dashboard layout, the wording on screens and which modules are switched on. A template changes data and settings only. If a sector needs new code, that code becomes a module that templates can switch on.

| Template | Job titles | Starter KPIs | Modules on |
| --- | --- | --- | --- |
| Restaurant | Owner, branch manager, chef, waiter, cashier, kitchen helper | On-time attendance, customer rating, upsell rate, sales per shift, food waste | Shifts and attendance |
| Marketing agency | Account manager, designer, copywriter, strategist | Billable utilization, on-time delivery, client retention, leads generated | KPIs and targets |
| Real estate agency | Agent, team lead, administrator | Listings added, viewings held, deals closed, commission target | KPIs and targets |
| Health clinic, later | Doctor, nurse, receptionist | Patient wait time, appointment punctuality | Credential tracking, not yet built |

### User flows

**A new company signs up**

1. The owner creates an account and verifies their email.
2. The owner picks a sector, and the system loads that template.
3. The owner adds locations and confirms job titles, which are already filled in from the template.
4. The owner uploads a CSV of staff. A preview flags errors per row, the owner fixes them and confirms.
5. The system creates employee IDs and invites staff by phone number or email.
6. The owner lands on the dashboard, which shows headcount at once and performance as soon as targets exist.

**A manager plans the week**

1. The manager opens the weekly grid for their location and copies last week's plan.
2. The manager adjusts shifts, and the system warns about gaps and double bookings.
3. The manager publishes, and staff are told by their chosen channel.
4. A staff member requests a swap, and the manager approves or declines it.

**A staff member's day**

1. The employee logs in with email or a phone number and a one-time code.
2. They see today's shift and clock in. Arriving after the grace period flags the attendance as late.
3. They check their targets and enter a progress value when one is due.
4. They clock out at the end of the shift.

**An owner's weekly review**

1. The owner opens the company dashboard and filters by location and period.
2. The owner spots a branch with rising lateness or a target at risk.
3. The owner drills into that branch, then into the person, and exports the table to CSV if needed.

**A review period closes**

1. Targets lock when the period ends.
2. The system calculates final scores and stores them in each employee's history.
3. Managers use the performance tab to prepare for review conversations.
4. A new period starts, and managers assign new targets or carry existing ones forward.

**An employee leaves**

1. The admin marks the record inactive and sets an end date.
2. The login is disabled, and the person drops out of active rosters and dashboards.
3. Their history stays in place, and the audit log records the change.

### End-to-end product

The product is one web application with a side menu that changes by role.

| Role | Menu |
| --- | --- |
| Employee | Home, My Shifts, My Profile, My Performance, Directory |
| Supervisor | Everything above plus Today's Shift and Attendance |
| Manager | Everything above plus My Team, Schedule, Targets and Team Dashboard |
| HR admin and owner | Everything above plus People, Locations, KPI Library, Reports and Settings |
| Super admin | A separate console for companies, plans, usage and support |

Data moves in one direction. The admin creates the organization and the people. Managers build shifts and set targets. Employees clock in and record progress. The system calculates attendance, status and scores. Every dashboard reads from that same data, so nobody keeps a separate report.

**Core data objects**

- Company, Location and Employee
- Role and Permission
- Shift and Attendance record
- KPI, Target and Progress entry
- Review period
- Audit event
- Subscription and Plan

### Non-functional requirements

**Security.** All data is encrypted in transit and at rest. Passwords are hashed with a modern algorithm. Permissions are enforced at the API layer. Access to and changes of sensitive personal fields are logged. Tenant isolation is tested on every release.

**Privacy.** The product holds personal data, so it must support export and deletion requests from day one. Plan for India's DPDP Act and GDPR, and get a legal review before selling outside India.

**Performance.** Directory search returns in under one second for 1,000 records. Dashboards load in under three seconds for a company of 300 employees. Clock-in responds in under two seconds on a mobile connection.

**Reliability.** Daily backups with a tested restore, a recovery point of 24 hours or less, and monitoring with alerts.

**Accessibility.** Core flows meet WCAG 2.1 AA, with full keyboard navigation on forms and tables.

**Compatibility.** Current Chrome, Edge, Safari and Firefox. Staff screens are built phone first. Admin and import screens are built for desktop.

**Scalability.** The architecture supports 1,000 employees per company and 100 companies without redesign.

### Success metrics

Targets cover the first 90 days after a customer goes live and should be reset once real baselines exist.

**Adoption**

- At least 90 percent of staff log in within 30 days of invitation.
- At least 80 percent of managers log in weekly.
- At least 85 percent of shifts are clocked in through the app.

**Data quality**

- At least 95 percent of employee records have all core fields filled within 30 days of import.
- Fewer than 2 percent of CSV rows fail after the preview step.

**Performance process**

- At least 90 percent of staff have an active target within 45 days of go-live.
- At least 75 percent of scheduled progress updates arrive on time.
- At least 80 percent of review periods close within seven days of their end date.

**Customer value**

- Owners retire the staff spreadsheet or chat rota within 60 days.
- Managers cut weekly rota planning time by 40 percent, measured by a short survey.
- Satisfaction of 4 out of 5 or higher in an in-app survey at 30 and 90 days.

**Business**

- Trial to paid conversion of at least 25 percent, as a starting target.
- Monthly customer churn below 3 percent after the first six months.
- At least two paying restaurants before the second sector template is built.

**Quality and trust**

- Monthly availability of at least 99.5 percent.
- Zero incidents where one company sees another company's data, or a user sees data their role does not allow.

The last item is a release blocker and not a soft target. One breach would end trust in a product that holds personal data.

### Release plan

The plan assumes two engineers, one designer and one product manager, starting after the restaurant meeting. Validate the timing with engineering before committing to a date.

| Phase | Weeks | What ships | Gate to move on |
| --- | --- | --- | --- |
| 1. Harden the foundation | 1 to 4 | Tenant isolation, authentication, roles, audit log, backups, CSV import and export | Isolation tests pass and a security review finds no open serious issues |
| 2. Complete the core | 5 to 9 | Profiles, field-level visibility, shifts, swaps, attendance, KPIs, targets, dashboards and notifications | The restaurant template runs end to end with real data |
| 3. Add the SaaS layer | 10 to 12 | Signup, free trial, billing, onboarding wizard, super admin console and usage tracking | A new test company signs up and pays without help from us |
| 4. Pilot | 13 to 16 | First paying restaurant live, support routine, fixes from real use | Two weeks of daily use with no data incident |
| 5. Second sector | After two paying restaurants | Agency or real estate template and the sector selector | Template goes live for a pilot customer in under one week of work |

### Risks

- Staff may not adopt the app if clocking in feels like surveillance. Explain what is tracked and who sees it, and keep individual data limited to the person, their manager and the admin.
- Scheduling tools already exist, so our edge has to be staff records, attendance and performance in one place. Confirm this with the owner before building further.
- Hourly staff often share phones or change numbers. Phone login needs a clear recovery path.
- Imported data will arrive messy. The preview step and clear error messages are the defence.
- Requests for payroll, leave and hiring will start early. The list below is how we hold the line.
- A security mistake in a multi-company product affects every customer at once, which is why isolation tests sit in phase 1.

### Open questions

- What does the restaurant owner pay today, and what would he pay for this?
- Does he need Hindi or another local language in the staff screens?
- Which channel do his staff actually read, SMS or WhatsApp?
- Should clock-in be limited to the branch location?
- How should targets behave when someone changes branch mid-period?

### What production does not build in version one

- Payroll, tips and compensation management
- Leave balances and full time-off management
- Recruitment and applicant tracking
- Onboarding and offboarding checklists
- Benefits and insurance administration
- 360-degree feedback and peer reviews
- Learning and training management
- Automatic KPI pulls from POS, CRM or analytics tools
- Native mobile apps
- Custom workflow builders and approval chains
- AI-written summaries or recommendations
- Labor-law compliance tooling for any country
- Public API and third-party marketplace
- The health clinic template and credential tracking

Any request on this list goes into a backlog with the requesting customer noted, and is reviewed at the end of phase 4.

## From Showcase to Production

The showcase code is the starting point for production, and the foundation rules in Part 1 are what make that possible. This table shows what carries over untouched, what gets hardened and what is new.

| Area | Showcase | Production | Change |
| --- | --- | --- | --- |
| Company ID on every record | One company | Many companies, isolated and tested | Hardened |
| Roles and permissions | Four roles checked on the server | Same roles plus super admin, audit log and optional custom roles | Hardened |
| Staff login | Phone number with a simulated code | Real SMS or WhatsApp codes and email login | Rebuilt |
| Employee records and profiles | Core fields and sample data | Import, duplicate detection, field-level visibility and history | Extended |
| Shifts and attendance | Weekly grid and clock-in | Templates, swaps, reports and optional location checks | Extended |
| KPIs and targets | Fixed starter set | Editable library, weighting, periods and templates | Extended |
| Dashboards | Owner and staff views | Role-based views, branch comparison and exports | Extended |
| Notifications | None | Email and phone channels with reminders | New |
| Signup, trial and billing | None | Full self-serve flow | New |
| Sector templates | Restaurant data hardcoded as defaults | Template system with a sector selector | New |
| Backups, monitoring and security review | None | Required before first paying customer | New |

Two rules keep the parts from drifting apart. When the restaurant meeting ends, move anything the owner asked for into Part 2 and mark it must-have or nice-to-have. When production work starts, treat Part 1 as frozen history and make every later change in Part 2.

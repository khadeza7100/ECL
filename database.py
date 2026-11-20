import mysql.connector

# ==========================================
# 1. MYSQL DATABASE CONFIGURATION
# ==========================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Khadem700++##",
    "database": "ecl_db",
    "port": 3306
}

# ==========================================
# 2. IN-MEMORY STORAGE FALLBACKS
# ==========================================
local_corporate_db = {}
local_individual_db = {}
local_collateral_db = {}
local_credit_ratings_db = {}
local_funded_ac_db = {}
local_non_funded_ac_db = {}
local_ccf_db = {}

def get_db_connection():
    """Establishes and returns a connection to MySQL."""
    return mysql.connector.connect(**DB_CONFIG)

# ==========================================
# 3. DATABASE INITIALIZATION & AUTO-MIGRATIONS
# ==========================================
def init_db():
    """Initializes database tables and migrates missing columns automatically."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Economic Variables Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economic_variables (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year VARCHAR(10) NOT NULL,
                variable_name VARCHAR(100) NOT NULL,
                value DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_year_var (year, variable_name)
            )
        ''')

        # Discounting Factor Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discounting_factors (
                id INT PRIMARY KEY DEFAULT 1,
                factor_val DECIMAL(10, 4) DEFAULT 0.0000,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT single_row CHECK (id = 1)
            )
        ''')

        # Credit Conversion Factors Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_conversion_factors (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year VARCHAR(10) NOT NULL,
                facility_type VARCHAR(50) NOT NULL,
                facility_issued DECIMAL(15, 2) DEFAULT 0.00,
                demand_loan_created DECIMAL(15, 2) DEFAULT 0.00,
                cc_rate DECIMAL(10, 4) DEFAULT 0.0000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_year_facility (year, facility_type)
            )
        ''')

        # Individual Profiles Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS individual_profiles (
                customer_number VARCHAR(50) PRIMARY KEY,
                customer_name VARCHAR(150),
                legal_entity VARCHAR(50),
                district VARCHAR(50),
                gender VARCHAR(20),
                religion VARCHAR(50),
                marital_status VARCHAR(50),
                dob VARCHAR(30),
                education VARCHAR(50),
                occupation VARCHAR(50),
                salary_income DECIMAL(15, 2) DEFAULT 0.00,
                other_income DECIMAL(15, 2) DEFAULT 0.00,
                monthly_installment DECIMAL(15, 2) DEFAULT 0.00,
                family_expense DECIMAL(15, 2) DEFAULT 0.00,
                income_expense_ratio DECIMAL(10, 2) DEFAULT 0.00,
                total_asset DECIMAL(15, 2) DEFAULT 0.00,
                total_liability DECIMAL(15, 2) DEFAULT 0.00,
                net_worth DECIMAL(15, 2) DEFAULT 0.00,
                default_history VARCHAR(20),
                repayment_behavior VARCHAR(50),
                cib_status VARCHAR(50),
                audit_objection VARCHAR(20),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # Corporate Profiles Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_profiles (
                customer_number VARCHAR(50) PRIMARY KEY,
                customer_name VARCHAR(150),
                legal_entity VARCHAR(50),
                business_type VARCHAR(50),
                fixed_asset DECIMAL(15, 2) DEFAULT 0.00,
                manpower_count INT DEFAULT 0,
                business_turnover DECIMAL(15, 2) DEFAULT 0.00,
                business_size VARCHAR(50),
                category VARCHAR(100),
                business_sector VARCHAR(100),
                product_service_name VARCHAR(150),
                location_district VARCHAR(50),
                default_history VARCHAR(20),
                repayment_behavior VARCHAR(50),
                cib_status VARCHAR(50),
                audit_objection VARCHAR(20),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # Collateral Profiles Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collateral_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                customer_number VARCHAR(50) NOT NULL,
                customer_name VARCHAR(150),
                security_type VARCHAR(50),
                quantity DECIMAL(15, 2) DEFAULT 0.00,
                measurement_unit VARCHAR(50),
                valuation_date VARCHAR(30),
                market_value DECIMAL(15, 2) DEFAULT 0.00,
                fsv DECIMAL(15, 2) DEFAULT 0.00,
                collateral_quality VARCHAR(50),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_cust_num (customer_number)
            )
        ''')

        # Collateral Haircuts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collateral_haircuts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year VARCHAR(10) NOT NULL,
                property_type VARCHAR(50) NOT NULL,
                market_value DECIMAL(15, 2) DEFAULT 0.00,
                liquidation_value DECIMAL(15, 2) DEFAULT 0.00,
                haircut_rate DECIMAL(10, 4) DEFAULT 0.0000,
                liquidation_time_years DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_year_property (year, property_type)
            )
        ''')

        # Credit Ratings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_ratings (
                customer_number VARCHAR(50) PRIMARY KEY,
                customer_name VARCHAR(150),
                year_financials VARCHAR(10),
                current_ratio DECIMAL(10, 2) DEFAULT 0.00,
                net_profit_margin DECIMAL(10, 2) DEFAULT 0.00,
                icr DECIMAL(10, 2) DEFAULT 0.00,
                dscr DECIMAL(10, 2) DEFAULT 0.00,
                debt_equity DECIMAL(10, 2) DEFAULT 0.00,
                fin_debt_nw DECIMAL(10, 2) DEFAULT 0.00,
                icrrs_rating VARCHAR(50),
                icrrs_year VARCHAR(10),
                rating_company VARCHAR(50),
                short_term_rating VARCHAR(50),
                long_term_rating VARCHAR(50),
                rating_year VARCHAR(10),
                rating_expiry_date VARCHAR(10),
                scoring VARCHAR(50),
                scoring_year VARCHAR(10),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute("SHOW COLUMNS FROM credit_ratings")
        credit_ratings_existing_cols = [col[0] for col in cursor.fetchall()]
        if "rating_company" not in credit_ratings_existing_cols:
            cursor.execute("ALTER TABLE credit_ratings ADD COLUMN rating_company VARCHAR(50) AFTER icrrs_year")
        if "rating_expiry_date" not in credit_ratings_existing_cols:
            cursor.execute("ALTER TABLE credit_ratings ADD COLUMN rating_expiry_date VARCHAR(10) AFTER rating_year")

# Auto-Migration Checks for funded_ac_profiles
        cursor.execute("SHOW COLUMNS FROM funded_ac_profiles")
        funded_existing_cols = [col[0] for col in cursor.fetchall()]

        if "overdue_install" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN overdue_install DECIMAL(10, 2) DEFAULT 0.00 AFTER install_recovered")
        if "overdue_amt" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN overdue_amt DECIMAL(15, 2) DEFAULT 0.00 AFTER overdue_in_days")
        if "ead" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN ead DECIMAL(15, 2) DEFAULT 0.00 AFTER ecl_category")
        if "staging_by_dpd" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN staging_by_dpd VARCHAR(50) AFTER ead")
        if "sicr_impairment" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN sicr_impairment VARCHAR(50) AFTER staging_by_dpd")
        if "qj_stage" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN qj_stage VARCHAR(50) AFTER sicr_impairment")
        if "qj_reason" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN qj_reason TEXT AFTER qj_stage")

# Funded A/C Profiles Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS funded_ac_profiles (
                ac_num VARCHAR(50) PRIMARY KEY,
                reporting_date VARCHAR(30),
                cust_num VARCHAR(50),
                cust_name VARCHAR(150),
                nature VARCHAR(50),
                approval_type VARCHAR(50),
                approval_date VARCHAR(30),
                loan_limit DECIMAL(15, 2) DEFAULT 0.00,
                loan_out DECIMAL(15, 2) DEFAULT 0.00,
                accrued_int DECIMAL(15, 2) DEFAULT 0.00,
                calc_int DECIMAL(15, 2) DEFAULT 0.00,
                exp_date VARCHAR(30),
                first_inst_due VARCHAR(30),
                due_install DECIMAL(10, 2) DEFAULT 0.00,
                install_size DECIMAL(15, 2) DEFAULT 0.00,
                amt_recovered DECIMAL(15, 2) DEFAULT 0.00,
                install_recovered DECIMAL(10, 2) DEFAULT 0.00,
                overdue_install DECIMAL(10, 2) DEFAULT 0.00,
                overdue_in_days INT DEFAULT 0,
                overdue_amt DECIMAL(15, 2) DEFAULT 0.00,
                ecl_category VARCHAR(100),
                ead DECIMAL(15, 2) DEFAULT 0.00,
                staging_by_dpd VARCHAR(50),
                sicr_impairment VARCHAR(50),
                qj_stage VARCHAR(50),
                qj_reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # Non-Funded A/C Profiles Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS non_funded_ac_profiles (
                ac_num VARCHAR(50) PRIMARY KEY,
                reporting_date VARCHAR(30),
                cust_num VARCHAR(50),
                cust_name VARCHAR(150),
                cont_type VARCHAR(50),
                amt_liability DECIMAL(15, 2) DEFAULT 0.00,
                issue_date VARCHAR(30),
                exp_date VARCHAR(30),
                overdue_days INT DEFAULT 0,
                margin_kept DECIMAL(15, 2) DEFAULT 0.00,
                ac_limit DECIMAL(15, 2) DEFAULT 0.00,
                ccf VARCHAR(50),
                ead DECIMAL(15, 2) DEFAULT 0.00,
                staging_by_dpd VARCHAR(50),
                sicr_impairment VARCHAR(50),
                qj_stage VARCHAR(50),
                qj_reason TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')

        # Loan Staging Criteria Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_staging_criteria (
                id INT PRIMARY KEY DEFAULT 1,
                dpd_stage1 VARCHAR(50) DEFAULT '<=30',
                dpd_stage2 VARCHAR(50) DEFAULT '>30 AND <=90',
                dpd_stage3 VARCHAR(50) DEFAULT '>90',
                qj_stage2 VARCHAR(100) DEFAULT 'SICR',
                qj_stage3 VARCHAR(100) DEFAULT 'Impairment',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT single_criteria CHECK (id = 1)
            )
        ''')

        # Auto-Migration Checks
        cursor.execute("SHOW COLUMNS FROM collateral_profiles")
        col_existing_cols = [col[0] for col in cursor.fetchall()]
        if "fsv" not in col_existing_cols:
            cursor.execute("ALTER TABLE collateral_profiles ADD COLUMN fsv DECIMAL(15, 2) DEFAULT 0.00 AFTER market_value")

        cursor.execute("SHOW COLUMNS FROM funded_ac_profiles")
        funded_existing_cols = [col[0] for col in cursor.fetchall()]

        if "overdue_install" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN overdue_install DECIMAL(10, 2) DEFAULT 0.00 AFTER install_recovered")
        if "overdue_amt" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN overdue_amt DECIMAL(15, 2) DEFAULT 0.00 AFTER overdue_in_days")
        if "ead" not in funded_existing_cols:
            cursor.execute("ALTER TABLE funded_ac_profiles ADD COLUMN ead DECIMAL(15, 2) DEFAULT 0.00 AFTER ecl_category")

        cursor.execute("SHOW COLUMNS FROM non_funded_ac_profiles")
        nf_existing_cols = [col[0] for col in cursor.fetchall()]

        if "ac_limit" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN ac_limit DECIMAL(15, 2) DEFAULT 0.00 AFTER margin_kept")
        if "ccf" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN ccf VARCHAR(50) AFTER ac_limit")
        if "ead" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN ead DECIMAL(15, 2) DEFAULT 0.00 AFTER ccf")
        if "staging_by_dpd" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN staging_by_dpd VARCHAR(50) AFTER ead")
        if "sicr_impairment" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN sicr_impairment VARCHAR(50) AFTER staging_by_dpd")
        if "qj_stage" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN qj_stage VARCHAR(50) AFTER sicr_impairment")
        if "qj_reason" not in nf_existing_cols:
            cursor.execute("ALTER TABLE non_funded_ac_profiles ADD COLUMN qj_reason TEXT AFTER qj_stage")

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 4. CROSS-TABLE VALIDATION & HELPER FUNCTIONS
# ==========================================

def get_customer_name_by_number(customer_number):
    """Searches individual and corporate tables using exact character matching for customer_number."""
    cust_num = str(customer_number).strip()
    if not cust_num:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT customer_name FROM individual_profiles WHERE TRIM(customer_number) = %s", (cust_num,))
        res = cursor.fetchone()
        if res:
            cursor.close()
            conn.close()
            return res["customer_name"]

        cursor.execute("SELECT customer_name FROM corporate_profiles WHERE TRIM(customer_number) = %s", (cust_num,))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        if res:
            return res["customer_name"]
    except Exception:
        pass
    return None

def is_customer_exists_in_table(customer_number, target_table):
    cust_num = str(customer_number).strip()
    if not cust_num:
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"SELECT COUNT(*) FROM {target_table} WHERE TRIM(customer_number) = %s"
        cursor.execute(query, (cust_num,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception:
        return False

def is_account_exists_in_table(ac_num, target_table):
    account_no = str(ac_num).strip()
    if not account_no:
        return False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"SELECT COUNT(*) FROM {target_table} WHERE TRIM(ac_num) = %s"
        cursor.execute(query, (account_no,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count > 0
    except Exception:
        return False

def check_duplicate_account_number(ac_num):
    account_no = str(ac_num).strip()
    if not account_no:
        return {"exists_in_funded": False, "exists_in_non_funded": False}
    
    return {
        "exists_in_funded": is_account_exists_in_table(account_no, "funded_ac_profiles"),
        "exists_in_non_funded": is_account_exists_in_table(account_no, "non_funded_ac_profiles")
    }

# ==========================================
# 5. ECONOMIC VARIABLES CRUD
# ==========================================

def save_economic_variables(year, variables_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO economic_variables (year, variable_name, value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE value = VALUES(value)
        '''
        data_tuples = []
        for var_name, value_str in variables_dict.items():
            val = round(float(value_str), 2) if value_str and str(value_str).strip() != "" else 0.00
            data_tuples.append((str(year).strip(), str(var_name).strip(), val))
            
        cursor.executemany(query, data_tuples)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_economic_variables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT year, variable_name, value FROM economic_variables")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        full_map = {}
        for row in results:
            y, k, v = str(row["year"]).strip(), str(row["variable_name"]).strip(), row["value"]
            if y not in full_map: full_map[y] = {}
            full_map[y][k] = f"{float(v):.2f}" if v is not None else ""
        return full_map
    except Exception:
        return {}

def get_economic_variables_by_year(year):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT variable_name, value FROM economic_variables WHERE TRIM(CAST(year AS CHAR)) = %s", (str(year).strip(),))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        data_map = {}
        for row in results:
            data_map[str(row["variable_name"]).strip()] = f"{float(row['value']):.2f}" if row["value"] is not None else ""
        return data_map
    except Exception:
        return {}

def delete_economic_variables_by_year(year):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM economic_variables WHERE TRIM(CAST(year AS CHAR)) = %s", (str(year).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 6. DISCOUNTING FACTOR CRUD
# ==========================================

def save_discounting_factor(value: float):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO discounting_factors (id, factor_val)
            VALUES (1, %s)
            ON DUPLICATE KEY UPDATE factor_val = VALUES(factor_val)
        '''
        cursor.execute(query, (float(value),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_discounting_factor():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT factor_val FROM discounting_factors WHERE id = 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and result["factor_val"] is not None:
            return float(result["factor_val"])
        return None
    except Exception:
        return None

# ==========================================
# 7. CREDIT CONVERSION FACTORS CRUD
# ==========================================

def save_credit_conversion_factor(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO credit_conversion_factors (
                year, facility_type, facility_issued, demand_loan_created, cc_rate
            ) VALUES (
                %(year)s, %(facility_type)s, %(facility_issued)s, %(demand_loan_created)s, %(cc_rate)s
            ) ON DUPLICATE KEY UPDATE
                facility_issued = VALUES(facility_issued),
                demand_loan_created = VALUES(demand_loan_created),
                cc_rate = VALUES(cc_rate)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_credit_conversion_factors():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_conversion_factors ORDER BY year DESC, facility_type ASC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

def delete_credit_conversion_factor(year, facility_type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM credit_conversion_factors WHERE TRIM(year) = %s AND TRIM(facility_type) = %s",
            (str(year).strip(), str(facility_type).strip())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 8. STAGE MIGRATION RATE CRUD
# ==========================================

def save_stage_migration_rate(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stage_migration_rates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year VARCHAR(10) NOT NULL,
                month VARCHAR(10) NOT NULL DEFAULT '',
                migrated_from VARCHAR(50) NOT NULL,
                migrated_to VARCHAR(50) NOT NULL DEFAULT '',
                num_migrated INT DEFAULT 0,
                total_ac_stage INT DEFAULT 0,
                migration_rate DECIMAL(10, 4) DEFAULT 0.0000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_year_month_from_to (year, month, migrated_from, migrated_to)
            )
        ''')

        cursor.execute("SHOW COLUMNS FROM stage_migration_rates")
        existing_columns = {column[0] for column in cursor.fetchall()}
        if "month" not in existing_columns:
            cursor.execute("ALTER TABLE stage_migration_rates ADD COLUMN month VARCHAR(10) NOT NULL DEFAULT '' AFTER year")
        if "migrated_to" not in existing_columns:
            cursor.execute("ALTER TABLE stage_migration_rates ADD COLUMN migrated_to VARCHAR(50) NOT NULL DEFAULT '' AFTER migrated_from")

        cursor.execute("SHOW INDEX FROM stage_migration_rates")
        existing_indexes = {index[2] for index in cursor.fetchall()}
        if "unique_year_migrated_from" in existing_indexes:
            cursor.execute("ALTER TABLE stage_migration_rates DROP INDEX unique_year_migrated_from")
        if "unique_year_month_from_to" not in existing_indexes:
            cursor.execute("ALTER TABLE stage_migration_rates ADD UNIQUE KEY unique_year_month_from_to (year, month, migrated_from, migrated_to)")
        
        if data_dict.get("id") is not None:
            query = '''
                UPDATE stage_migration_rates
                SET year = %(year)s,
                    month = %(month)s,
                    migrated_from = %(migrated_from)s,
                    migrated_to = %(migrated_to)s,
                    num_migrated = %(num_migrated)s,
                    total_ac_stage = %(total_ac_stage)s,
                    migration_rate = %(migration_rate)s
                WHERE id = %(id)s
            '''
        else:
            query = '''
                INSERT INTO stage_migration_rates (
                    year, month, migrated_from, migrated_to, num_migrated, total_ac_stage, migration_rate
                ) VALUES (
                    %(year)s, %(month)s, %(migrated_from)s, %(migrated_to)s, %(num_migrated)s, %(total_ac_stage)s, %(migration_rate)s
                ) ON DUPLICATE KEY UPDATE
                    num_migrated = VALUES(num_migrated),
                    total_ac_stage = VALUES(total_ac_stage),
                    migration_rate = VALUES(migration_rate)
            '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_stage_migration_rates():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM stage_migration_rates ORDER BY year DESC, month DESC, migrated_from ASC, migrated_to ASC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

def delete_stage_migration_rate(year, month, migrated_from, migrated_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM stage_migration_rates WHERE TRIM(year) = %s AND TRIM(month) = %s AND TRIM(migrated_from) = %s AND TRIM(migrated_to) = %s",
            (str(year).strip(), str(month).strip(), str(migrated_from).strip(), str(migrated_to).strip())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 9. LOAN STAGING CRITERIA CRUD
# ==========================================

def save_loan_staging_criteria(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO loan_staging_criteria (id, dpd_stage1, dpd_stage2, dpd_stage3, qj_stage2, qj_stage3)
            VALUES (1, %(dpd_stage1)s, %(dpd_stage2)s, %(dpd_stage3)s, %(qj_stage2)s, %(qj_stage3)s)
            ON DUPLICATE KEY UPDATE
                dpd_stage1 = VALUES(dpd_stage1),
                dpd_stage2 = VALUES(dpd_stage2),
                dpd_stage3 = VALUES(dpd_stage3),
                qj_stage2 = VALUES(qj_stage2),
                qj_stage3 = VALUES(qj_stage3)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_loan_staging_criteria():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loan_staging_criteria WHERE id = 1")
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        return res if res else {
            "dpd_stage1": "<=30",
            "dpd_stage2": ">30 AND <=90",
            "dpd_stage3": ">90",
            "qj_stage2": "SICR",
            "qj_stage3": "Impairment"
        }
    except Exception:
        return {
            "dpd_stage1": "<=30",
            "dpd_stage2": ">30 AND <=90",
            "dpd_stage3": ">90",
            "qj_stage2": "SICR",
            "qj_stage3": "Impairment"
        }

# ==========================================
# 10. INDIVIDUAL PROFILES CRUD
# ==========================================

def save_individual_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO individual_profiles (
                customer_number, customer_name, legal_entity, district, gender,
                religion, marital_status, dob, education, occupation,
                salary_income, other_income, monthly_installment, family_expense,
                income_expense_ratio, total_asset, total_liability, net_worth,
                default_history, repayment_behavior, cib_status, audit_objection
            ) VALUES (
                %(customer_number)s, %(customer_name)s, %(legal_entity)s, %(district)s, %(gender)s,
                %(religion)s, %(marital_status)s, %(dob)s, %(education)s, %(occupation)s,
                %(salary_income)s, %(other_income)s, %(monthly_installment)s, %(family_expense)s,
                %(income_expense_ratio)s, %(total_asset)s, %(total_liability)s, %(net_worth)s,
                %(default_history)s, %(repayment_behavior)s, %(cib_status)s, %(audit_objection)s
            ) ON DUPLICATE KEY UPDATE
                customer_name = VALUES(customer_name), legal_entity = VALUES(legal_entity),
                district = VALUES(district), gender = VALUES(gender), religion = VALUES(religion),
                marital_status = VALUES(marital_status), dob = VALUES(dob), education = VALUES(education),
                occupation = VALUES(occupation), salary_income = VALUES(salary_income), other_income = VALUES(other_income),
                monthly_installment = VALUES(monthly_installment), family_expense = VALUES(family_expense),
                income_expense_ratio = VALUES(income_expense_ratio), total_asset = VALUES(total_asset),
                total_liability = VALUES(total_liability), net_worth = VALUES(net_worth),
                default_history = VALUES(default_history), repayment_behavior = VALUES(repayment_behavior),
                cib_status = VALUES(cib_status), audit_objection = VALUES(audit_objection)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_individual_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM individual_profiles")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {str(row["customer_number"]).strip(): row for row in results}
    except Exception:
        return {}

def delete_individual_profile_by_id(customer_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM individual_profiles WHERE TRIM(customer_number) = %s", (str(customer_number).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 11. CORPORATE PROFILES CRUD
# ==========================================

def save_corporate_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO corporate_profiles (
                customer_number, customer_name, legal_entity, business_type,
                fixed_asset, manpower_count, business_turnover, business_size,
                category, business_sector, product_service_name, location_district,
                default_history, repayment_behavior, cib_status, audit_objection
            ) VALUES (
                %(customer_number)s, %(customer_name)s, %(legal_entity)s, %(business_type)s,
                %(fixed_asset)s, %(manpower_count)s, %(business_turnover)s, %(business_size)s,
                %(category)s, %(business_sector)s, %(product_service_name)s, %(location_district)s,
                %(default_history)s, %(repayment_behavior)s, %(cib_status)s, %(audit_objection)s
            ) ON DUPLICATE KEY UPDATE
                customer_name = VALUES(customer_name), legal_entity = VALUES(legal_entity),
                business_type = VALUES(business_type), fixed_asset = VALUES(fixed_asset),
                manpower_count = VALUES(manpower_count), business_turnover = VALUES(business_turnover),
                business_size = VALUES(business_size), category = VALUES(category),
                business_sector = VALUES(business_sector), product_service_name = VALUES(product_service_name),
                location_district = VALUES(location_district), default_history = VALUES(default_history),
                repayment_behavior = VALUES(repayment_behavior), cib_status = VALUES(cib_status),
                audit_objection = VALUES(audit_objection)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_corporate_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM corporate_profiles")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {str(row["customer_number"]).strip(): row for row in results}
    except Exception:
        return {}

def delete_corporate_profile_by_id(customer_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM corporate_profiles WHERE TRIM(customer_number) = %s", (str(customer_number).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 12. COLLATERAL PROFILES CRUD
# ==========================================

def save_collateral_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if data_dict.get("id"):
            query = '''
                UPDATE collateral_profiles SET
                    customer_number = %(customer_number)s,
                    customer_name = %(customer_name)s,
                    security_type = %(security_type)s,
                    quantity = %(quantity)s,
                    measurement_unit = %(measurement_unit)s,
                    valuation_date = %(valuation_date)s,
                    market_value = %(market_value)s,
                    fsv = %(fsv)s,
                    collateral_quality = %(collateral_quality)s
                WHERE id = %(id)s
            '''
        else:
            query = '''
                INSERT INTO collateral_profiles (
                    customer_number, customer_name, security_type, quantity,
                    measurement_unit, valuation_date, market_value, fsv,
                    collateral_quality
                ) VALUES (
                    %(customer_number)s, %(customer_name)s, %(security_type)s, %(quantity)s,
                    %(measurement_unit)s, %(valuation_date)s, %(market_value)s, %(fsv)s,
                    %(collateral_quality)s
                )
            '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_collateral_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM collateral_profiles ORDER BY customer_number ASC, id ASC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

def get_collateral_profiles_by_customer(customer_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM collateral_profiles WHERE TRIM(customer_number) = %s", (str(customer_number).strip(),))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

def delete_collateral_profile_by_id(record_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM collateral_profiles WHERE id = %s", (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 13. CREDIT RATINGS CRUD
# ==========================================

def save_credit_ratings_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO credit_ratings (
                customer_number, customer_name, year_financials, current_ratio,
                net_profit_margin, icr, dscr, debt_equity, fin_debt_nw,
                icrrs_rating, icrrs_year, rating_company, short_term_rating, long_term_rating,
                rating_year, rating_expiry_date, scoring, scoring_year
            ) VALUES (
                %(customer_number)s, %(customer_name)s, %(year_financials)s, %(current_ratio)s,
                %(net_profit_margin)s, %(icr)s, %(dscr)s, %(debt_equity)s, %(fin_debt_nw)s,
                %(icrrs_rating)s, %(icrrs_year)s, %(rating_company)s, %(short_term_rating)s, %(long_term_rating)s,
                %(rating_year)s, %(rating_expiry_date)s, %(scoring)s, %(scoring_year)s
            ) ON DUPLICATE KEY UPDATE
                customer_name = VALUES(customer_name),
                year_financials = VALUES(year_financials),
                current_ratio = VALUES(current_ratio),
                net_profit_margin = VALUES(net_profit_margin),
                icr = VALUES(icr),
                dscr = VALUES(dscr),
                debt_equity = VALUES(debt_equity),
                fin_debt_nw = VALUES(fin_debt_nw),
                icrrs_rating = VALUES(icrrs_rating),
                icrrs_year = VALUES(icrrs_year),
                rating_company = VALUES(rating_company),
                short_term_rating = VALUES(short_term_rating),
                long_term_rating = VALUES(long_term_rating),
                rating_year = VALUES(rating_year),
                rating_expiry_date = VALUES(rating_expiry_date),
                scoring = VALUES(scoring),
                scoring_year = VALUES(scoring_year)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_credit_ratings_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_ratings")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {str(row["customer_number"]).strip(): row for row in results}
    except Exception:
        return {}

def delete_credit_ratings_profile_by_id(customer_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM credit_ratings WHERE TRIM(customer_number) = %s", (str(customer_number).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 14. COLLATERAL HAIRCUT CRUD
# ==========================================

def save_collateral_haircut(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collateral_haircuts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                year VARCHAR(10) NOT NULL,
                property_type VARCHAR(50) NOT NULL,
                market_value DECIMAL(15, 2) DEFAULT 0.00,
                liquidation_value DECIMAL(15, 2) DEFAULT 0.00,
                haircut_rate DECIMAL(10, 4) DEFAULT 0.0000,
                liquidation_time_years DECIMAL(10, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_year_property (year, property_type)
            )
        ''')
        
        query = '''
            INSERT INTO collateral_haircuts (
                year, property_type, market_value, liquidation_value, haircut_rate, liquidation_time_years
            ) VALUES (
                %(year)s, %(property_type)s, %(market_value)s, %(liquidation_value)s, %(haircut_rate)s, %(liquidation_time_years)s
            ) ON DUPLICATE KEY UPDATE
                market_value = VALUES(market_value),
                liquidation_value = VALUES(liquidation_value),
                haircut_rate = VALUES(haircut_rate),
                liquidation_time_years = VALUES(liquidation_time_years)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_collateral_haircuts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM collateral_haircuts ORDER BY year DESC, property_type ASC")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception:
        return []

def delete_collateral_haircut(year, property_type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM collateral_haircuts WHERE TRIM(year) = %s AND TRIM(property_type) = %s",
            (str(year).strip(), str(property_type).strip())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 15. FUNDED A/C PROFILES CRUD
# ==========================================

def save_funded_ac_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO funded_ac_profiles (
                ac_num, reporting_date, cust_num, cust_name, nature,
                approval_type, approval_date, loan_limit, loan_out,
                accrued_int, calc_int, exp_date, first_inst_due,
                due_install, install_size, amt_recovered, install_recovered,
                overdue_install, overdue_in_days, overdue_amt, ecl_category, ead,
                staging_by_dpd, sicr_impairment, qj_stage, qj_reason
            ) VALUES (
                %(ac_num)s, %(reporting_date)s, %(cust_num)s, %(cust_name)s, %(nature)s,
                %(approval_type)s, %(approval_date)s, %(loan_limit)s, %(loan_out)s,
                %(accrued_int)s, %(calc_int)s, %(exp_date)s, %(first_inst_due)s,
                %(due_install)s, %(install_size)s, %(amt_recovered)s, %(install_recovered)s,
                %(overdue_install)s, %(overdue_in_days)s, %(overdue_amt)s, %(ecl_category)s, %(ead)s,
                %(staging_by_dpd)s, %(sicr_impairment)s, %(qj_stage)s, %(qj_reason)s
            ) ON DUPLICATE KEY UPDATE
                reporting_date = VALUES(reporting_date),
                cust_num = VALUES(cust_num),
                cust_name = VALUES(cust_name),
                nature = VALUES(nature),
                approval_type = VALUES(approval_type),
                approval_date = VALUES(approval_date),
                loan_limit = VALUES(loan_limit),
                loan_out = VALUES(loan_out),
                accrued_int = VALUES(accrued_int),
                calc_int = VALUES(calc_int),
                exp_date = VALUES(exp_date),
                first_inst_due = VALUES(first_inst_due),
                due_install = VALUES(due_install),
                install_size = VALUES(install_size),
                amt_recovered = VALUES(amt_recovered),
                install_recovered = VALUES(install_recovered),
                overdue_install = VALUES(overdue_install),
                overdue_in_days = VALUES(overdue_in_days),
                overdue_amt = VALUES(overdue_amt),
                ecl_category = VALUES(ecl_category),
                ead = VALUES(ead),
                staging_by_dpd = VALUES(staging_by_dpd),
                sicr_impairment = VALUES(sicr_impairment),
                qj_stage = VALUES(qj_stage),
                qj_reason = VALUES(qj_reason)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_funded_ac_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM funded_ac_profiles")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {str(row["ac_num"]).strip(): row for row in results}
    except Exception:
        return {}

def delete_funded_ac_profile_by_id(ac_num):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM funded_ac_profiles WHERE TRIM(ac_num) = %s", (str(ac_num).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 16. NON-FUNDED A/C PROFILES CRUD
# ==========================================

def save_non_funded_ac_profile(data_dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            INSERT INTO non_funded_ac_profiles (
                ac_num, reporting_date, cust_num, cust_name, cont_type,
                amt_liability, issue_date, exp_date, overdue_days, margin_kept,
                ac_limit, ccf, ead, staging_by_dpd, sicr_impairment, qj_stage, qj_reason
            ) VALUES (
                %(ac_num)s, %(reporting_date)s, %(cust_num)s, %(cust_name)s, %(cont_type)s,
                %(amt_liability)s, %(issue_date)s, %(exp_date)s, %(overdue_days)s, %(margin_kept)s,
                %(ac_limit)s, %(ccf)s, %(ead)s, %(staging_by_dpd)s, %(sicr_impairment)s, %(qj_stage)s, %(qj_reason)s
            ) ON DUPLICATE KEY UPDATE
                reporting_date = VALUES(reporting_date),
                cust_num = VALUES(cust_num),
                cust_name = VALUES(cust_name),
                cont_type = VALUES(cont_type),
                amt_liability = VALUES(amt_liability),
                issue_date = VALUES(issue_date),
                exp_date = VALUES(exp_date),
                overdue_days = VALUES(overdue_days),
                margin_kept = VALUES(margin_kept),
                ac_limit = VALUES(ac_limit),
                ccf = VALUES(ccf),
                ead = VALUES(ead),
                staging_by_dpd = VALUES(staging_by_dpd),
                sicr_impairment = VALUES(sicr_impairment),
                qj_stage = VALUES(qj_stage),
                qj_reason = VALUES(qj_reason)
        '''
        cursor.execute(query, data_dict)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

def get_all_non_funded_ac_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM non_funded_ac_profiles")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return {str(row["ac_num"]).strip(): row for row in results}
    except Exception:
        return {}

def delete_non_funded_ac_profile_by_id(ac_num):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM non_funded_ac_profiles WHERE TRIM(ac_num) = %s", (str(ac_num).strip(),))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise e

# ==========================================
# 17. LOCAL IN-MEMORY STORAGE HELPERS
# ==========================================

def save_local_profile(db_category, item_id, data_dict):
    category_map = {
        "corporate": local_corporate_db,
        "individual": local_individual_db,
        "collateral": local_collateral_db,
        "credit_ratings": local_credit_ratings_db,
        "funded_ac": local_funded_ac_db,
        "non_funded_ac": local_non_funded_ac_db,
        "ccf": local_ccf_db
    }
    target_db = category_map.get(db_category)
    if isinstance(target_db, dict):
        target_db[str(item_id)] = data_dict
        return True
    return False

def get_local_profile(db_category, item_id):
    category_map = {
        "corporate": local_corporate_db,
        "individual": local_individual_db,
        "collateral": local_collateral_db,
        "credit_ratings": local_credit_ratings_db,
        "funded_ac": local_funded_ac_db,
        "non_funded_ac": local_non_funded_ac_db,
        "ccf": local_ccf_db
    }
    target_db = category_map.get(db_category)
    if isinstance(target_db, dict):
        return target_db.get(str(item_id), {})
    return {}

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    init_db()
    print("Database initialization and migrations completed successfully.")
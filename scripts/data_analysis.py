import pandas as pd
from scipy.stats import ttest_ind

# Load the dataset
file_path = "/Users/benito/Documents/docs/proj/OpenDataMA/data/rej_with_masssave_participation_table.csv"
data = pd.read_csv(file_path)

# 1. Significant difference in participation rates between REJ and non-REJ
rej = data[data['REJ__flag_'] == 1.0]
non_rej = data[data['REJ__flag_'] == 0.0]

# T-test for electric participation rates
t_stat_electric, p_value_electric = ttest_ind(rej['electric_participation_rate_avg'], non_rej['electric_participation_rate_avg'], nan_policy='omit')

# T-test for gas participation rates
t_stat_gas, p_value_gas = ttest_ind(rej['gas_participation_rate_avg'], non_rej['gas_participation_rate_avg'], nan_policy='omit')

print("T-Test Results:")
print(f"Electric Participation Rate: t-statistic = {t_stat_electric}, p-value = {p_value_electric}")
print(f"Gas Participation Rate: t-statistic = {t_stat_gas}, p-value = {p_value_gas}")

# 2. Mean participation rates for specific flags
mean_electric_zvhh = data[data['ZVHH_flag'] == 1.0]['electric_participation_rate_avg'].mean()
mean_gas_zvhh = data[data['ZVHH_flag'] == 1.0]['gas_participation_rate_avg'].mean()

mean_electric_senior = data[data['Senior_fla'] == 1.0]['electric_participation_rate_avg'].mean()
mean_gas_senior = data[data['Senior_fla'] == 1.0]['gas_participation_rate_avg'].mean()

mean_electric_disability = data[data['Disabili_f'] == 1.0]['electric_participation_rate_avg'].mean()
mean_gas_disability = data[data['Disabili_f'] == 1.0]['gas_participation_rate_avg'].mean()

print("\nMean Participation Rates for Specific Flags:")
print(f"Zero Vehicle Households - Electric: {mean_electric_zvhh}, Gas: {mean_gas_zvhh}")
print(f"High Senior Rate - Electric: {mean_electric_senior}, Gas: {mean_gas_senior}")
print(f"High Disability Rate - Electric: {mean_electric_disability}, Gas: {mean_gas_disability}")

# 3. Mean participation rates across all tracts
mean_electric_all = data['electric_participation_rate_avg'].mean()
mean_gas_all = data['gas_participation_rate_avg'].mean()

print("\nMean Participation Rates Across All Tracts:")
print(f"Electric: {mean_electric_all}, Gas: {mean_gas_all}")

# 4. Mean population across all tracts
mean_population = data['POPULATION'].mean()

print("\nMean Population Across All Tracts:")
print(f"Population: {mean_population}")
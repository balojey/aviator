import csv
import hashlib

def verify_fairness(data_row):
    """
    Verifies if the game result is fair by recomputing the hash and checking if it matches the stored hash.
    :param data_row: List containing a single row of data.
    :return: Boolean indicating fairness.
    """
    server_seed, player_seed_1, player_seed_2, player_seed_3, stored_hash, multiplier = (
        data_row[3], data_row[4], data_row[5], data_row[6], data_row[7], float(data_row[8])
    )
    
    # Concatenate the seeds in the order they are used
    combined_string = server_seed + player_seed_1 + player_seed_2 + player_seed_3
    
    # Compute SHA-512 hash
    computed_hash = hashlib.sha512(combined_string.encode()).hexdigest()
    
    # Check if the computed hash matches the stored hash
    is_fair = computed_hash == stored_hash
    
    return is_fair

def verify_multiplier(data_row):
    """
    Verifies if the multiplier produced aligns with the expected computation.
    :param data_row: List containing a single row of data.
    :return: Boolean indicating if the multiplier is accurate.
    """
    stored_hash, multiplier = data_row[7], float(data_row[8])
    
    # Convert the hash to an integer and derive a multiplier (Example logic, adjust if needed)
    hash_int = int(stored_hash[:13], 16)  # Take first 13 hex characters and convert to integer
    computed_multiplier = max(1.00, (hash_int % 1000) / 100.0)  # Normalize to a reasonable multiplier range
    
    return round(computed_multiplier, 2) == round(multiplier, 2)


if __name__ == '__main__':
    with open('sporty_aviator_data.csv', 'r', newline='') as file:
        reader = csv.reader(file)

        print(f"Number of fair games: {sum(verify_fairness(row) for row in reader)}")
        print(f"Number of correct multipliers: {sum(verify_multiplier(row) for row in reader)}")
import csv
from datetime import datetime

def filter_by_time_range(csv_file, start_time, end_time):
    """
    Reads the CSV file and filters out rows that are outside the given time range.
    :param csv_file: Path to the CSV file.
    :param start_time: Start time as a string in HH:MM:SS format.
    :param end_time: End time as a string in HH:MM:SS format.
    """
    start_time = datetime.strptime(start_time, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time, "%H:%M:%S").time()
    
    filtered_data = []
    
    with open(csv_file, 'r', newline='') as file:
        reader = csv.reader(file)
        
        for row in reader:
            row_time = datetime.strptime(row[2], "%H:%M:%S").time()
            
            if start_time <= row_time <= end_time:
                filtered_data.append(row)
    
    # Write filtered data back to a new file
    output_file = "filtered_" + csv_file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(filtered_data)  # Write filtered rows
    
    print(f"Filtered data saved to {output_file}")
    return output_file


if __name__ == '__main__':
    output_file = filter_by_time_range('sporty_aviator_data.csv', '07:00:00', '10:00:00')

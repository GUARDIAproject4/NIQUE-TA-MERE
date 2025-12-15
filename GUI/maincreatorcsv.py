import csv


def read_csv(file_name):
    with open(file_name, mode='r') as file:
        csvFile = csv.reader(file)
        data = []
        for lines in csvFile:
            data.append(lines)
    return data


def create_csv(file_name, data):
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
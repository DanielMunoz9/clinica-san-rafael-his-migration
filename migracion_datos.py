import pandas as pd
from datetime import datetime
import logging

# Setting up logging
logging.basicConfig(filename='migracion_datos.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

def format_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception as e:
        logging.error(f"Date formatting error: {e} for date {date_str}")
        return None  # or some default value

def standardize_phone(phone):
    if phone.startswith('57'):
        return f"+{phone}"
    elif phone.startswith('0'):
        return f"+57{phone[1:]}"
    elif phone.isdigit():
        return f"+57{phone}"
    else:
        logging.error(f"Phone standardization error: {phone}")
        return None

def main():
    try:
        # Read the CSV file
        df = pd.read_csv('pacientes.csv')

        # Unifying nombre and apellido into nombre_completo
        df['nombre_completo'] = df['nombre'] + ' ' + df['apellido']

        # Converting dates to DD/MM/YYYY format
        for date_column in ['fecha_nacimiento', 'fecha_registro']:  # Example date columns
            df[date_column] = df[date_column].apply(format_date)

        # Removing duplicates
        df.drop_duplicates(subset=['correo', 'telefono'], inplace=True)

        # Validating required fields
        required_fields = ['nombre', 'apellido', 'correo', 'telefono']
        for field in required_fields:
            if df[field].isnull().any():
                logging.error(f"Missing required field: {field}")

        # Standardizing phone numbers
        df['telefono'] = df['telefono'].apply(standardize_phone)

        # Exporting the cleaned data
        df.to_csv('Migracion_DanielMunoz9.csv', index=False)
        logging.info("Data migration completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
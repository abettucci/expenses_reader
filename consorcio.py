from googleapiclient.discovery import build
import pandas as pd
import json
from oauth2client.service_account import ServiceAccountCredentials
import boto3
import re
from botocore.exceptions import ClientError
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

def cargar_datos_df(gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura):
    data = {
        "nro_sheets" : nro_sheets,
        "titulo" : titulo,
        "subtitulo" : subtitulo,
        "proveedor" : proveedor,
        "detalles" : detalles,
        "gasto_comun" : gasto_comun,
        "gasto_vivienda" : gasto_vivienda,
        "gasto_particular" : gasto_particular,
        "saldo_impago" : saldo_impago,
        "periodo_devengado_a_pagar" : periodo_gasto,
        "categ_cuenta_a_pagar" : cuenta,
        "comprobante" : comprobante,
        "numero_cuit" : numero_cuit,
        "numero_cuil" : numero_cuil,
        "unidad_funcional" : uf,
        "tipo_factura" : tipo_factura,
        "numero_factura" : numero_factura,
        "fecha_de_pago_factura" :  fecha_de_pago_factura,
        "orden_de_pago_factura" : orden_de_pago_factura
    }
    
    # print('data_final: ', data)

    lista_data_gastos.append(data)
    gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None
    
    return lista_data_gastos, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura

def get_secret_value_aws(secret_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name="us-east-2")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return secret

# Define una función para obtener la lista de archivos en una carpeta
def obtener_archivos_en_carpeta(carpeta_id):
    resultados = []
    page_token = None
    while True:
        parametros = {
            'q': f"'{carpeta_id}' in parents",
            'fields': 'nextPageToken, files(id, name)',
            'pageSize': 100,  # Cambia esto si esperas más de 100 archivos en la carpeta
            'pageToken': page_token
        }
        response = drive_service.files().list(**parametros).execute()
        archivos = response.get('files', [])
        resultados.extend(archivos)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return resultados

def numero_a_mes(numero_mes):
    meses = {
        "01": "Enero", 
        "02": "Febrero", 
        "03": "Marzo", 
        "04": "Abril",
        "05": "Mayo", 
        "06": "Junio", 
        "07": "Julio", 
        "08": "Agosto",
        "09": "Septiembre", 
        "10": "Octubre", 
        "11": "Noviembre", 
        "12": "Diciembre"
    }
    return meses.get(numero_mes, "Mes inválido")

# Autenticación y creación de servicio para Google Drive y Sheets
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Obtenemos las credenciales de la API de MercadoLibre con un secreto del SecretManager de AWS pasandole la ruta del secreto
google_api_dict_list = []
google_key_locations = [
    'abettucci/MELIproject/Google_API_JSON_Key_File3',
    'abettucci/MELIproject/Google_API_JSON_Key_File']
for api_dict in google_key_locations:
    secret = get_secret_value_aws(api_dict)
    secret_data = json.loads(secret)
    key_dict = {
        "private_key_id" : secret_data.get('private_key_id'),
        "type" : secret_data.get('type'),
        "project_id" : secret_data.get('project_id'),
        "client_id" : secret_data.get('client_id'),
        "client_email" : secret_data.get('client_email'),
        "private_key" : secret_data.get('private_key')}
    google_api_dict_list.append(key_dict)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_api_dict_list[0], 
    ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

drive_service = build('drive', 'v3', credentials=creds)
sheets_service = build('sheets', 'v4', credentials=creds)

# ID de la carpeta de Google Drive y del Spreadsheet de destino
folder_id = '11QARWhgUwm9ZG-5oxw_ul0YcDUEGOD5B'
destination_spreadsheet_id = '1iIAXV4NIE3Vf-tcniCKakcuP42ZJ9iS_0n9mQrmBtfQ'
destination_sheet_name = 'Hoja 5'  # Cambia esto si el nombre de la hoja es diferente

# Obtener la última fila con datos en el Spreadsheet de destino
destination_result = sheets_service.spreadsheets().values().get(spreadsheetId=destination_spreadsheet_id, range=destination_sheet_name).execute()
destination_values = destination_result.get('values', [])
start_row = len(destination_values) + 1  # Determina el próximo número de fila disponible

# Aca deberiamos leer el nro_ticket del sheets destino y comparar contra los nro_ticket de los excels en la carpeta "Excels"
# para no repetir las filas
set_nro_sheets = set()
if destination_values:
    df = pd.DataFrame(destination_values[1:], columns=destination_values[0])  # Asumiendo que la primera fila son los encabezados
    lista_nro_sheets = df['nro_sheets'].unique().tolist()
    for val in lista_nro_sheets:
        set_nro_sheets.add(val)
    # print('Set de archivos ya cargados al sheets de expensas: ', set_nro_sheets)

# Buscar todos los archivos en la carpeta
files = obtener_archivos_en_carpeta(folder_id)

# Leer cada archivo y concatenar los datos en un DataFrame
df_list = []
total_sheets = None
cant_spreadsheets = 0
set_nombre_archivos_spreadsheet = set()

# Creo un set con todos los archivos spreadsheet diferentes que hay (sin duplicar)
# print('Listado archivos en carpeta:')
for file in files:
    spreadsheet_id = file['id']
    file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='*').execute()
    nombre_spreadsheet = file_metadata.get('name')
    # print(nombre_spreadsheet)
    if nombre_spreadsheet.startswith("https://docs.google.com/spreadsheets/d/rendicion-mes_"):
        nombre_archivo_spreadsheet = nombre_spreadsheet[len("https://docs.google.com/spreadsheets/d/"):]
        set_nombre_archivos_spreadsheet.add(nombre_archivo_spreadsheet)
        cant_spreadsheets += 1

# print('Listado google sheets que hay: ', set_nombre_archivos_spreadsheet)

# Itero en todos los archivos de la carpeta de drive, si encuentra un excel, y ademas no existe un spreadsheet con ese nombre, 
# lo convierte en spreadsheet y lo agrega al set de spreadsheets
for file in files:
    spreadsheet_id = file['id']
    file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='*').execute()
    nombre_spreadsheet = file_metadata.get('name')
    
    # Es un archivo de Excel .xlsx, lo convertimos a Sheet para poder leer bien los datos
    # Lo convertimos solo si no existe ya el mismo archivo pero con formato Google Sheets
    if nombre_spreadsheet.endswith(".xlsx") and nombre_spreadsheet.startswith("rendicion-mes_"):
        if nombre_spreadsheet[:-5] not in set_nombre_archivos_spreadsheet: # le sacamos el .xlsx para comparar
            if file_metadata.get('mimeType') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                # Subir el archivo y convertirlo en Google Spreadsheet
                file_metadata = {
                    'name': 'https://docs.google.com/spreadsheets/d/' + nombre_spreadsheet[:nombre_spreadsheet.find('.xlsx')],  # Nombre del nuevo archivo
                    'parents': [folder_id],
                    'mimeType': 'application/vnd.google-apps.spreadsheet'  # Especifica que debe ser un Google Spreadsheet
                }

                # Crear el nuevo archivo como Google Spreadsheet
                file = drive_service.files().copy(
                    fileId=spreadsheet_id,
                    body=file_metadata
                ).execute()

                spreadsheet_id = file['id']
                nombre_spreadsheet = file['name']

                # El nombre del spreadsheet creado a raiz del excel lo guardamos en el set de nombre de spreadsheets
                # por si mas adelante en la carpeta aparece otro excel con el mismo nombre y si no chequearamos esto,
                # estariamos vovliendo a crear el mismo spreadsheet con el set estatica del comienzo
                nombre_archivo_spreadsheet = nombre_spreadsheet[len("https://docs.google.com/spreadsheets/d/"):]
                set_nombre_archivos_spreadsheet.add(nombre_archivo_spreadsheet)

# print('Set de google sheets que hay: ', set_nombre_archivos_spreadsheet)

# Tenemos que volver a leer todos los archivos en la carpeta para que el objeto "Files" esté actualizado
files = obtener_archivos_en_carpeta(folder_id)
    
for file in files:
    spreadsheet_id = file['id']
    file_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='*').execute()
    nombre_spreadsheet = file_metadata.get('name')
    nombre_archivo_spreadsheet = nombre_spreadsheet[len("https://docs.google.com/spreadsheets/d/"):]

    print(nombre_spreadsheet)
    
    if nombre_archivo_spreadsheet in set_nombre_archivos_spreadsheet:
        if nombre_archivo_spreadsheet not in set_nro_sheets:
            sheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            total_sheets = sheet['sheets']
        
            empleados_fijos = [
                'CHAYZKA, GONZALO EZEQUIEL'
            ]

            titulos = [
                        'REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES', 
                        'GASTOS ORDINARIOS DEL PERÍODO (SUMINISTROS, SERVICIOS, ABONOS Y SEGUROS)',
                        'GASTOS PARTICULARES DEL PERÍODO',
                        'GASTOS DEVENGADOS PENDIENTES DE PAGO (CUENTAS POR PAGAR)']

            subtitulos = [
                        # GASTOS ORDINARIOS DEL PERÍODO (SUMINISTROS, SERVICIOS, ABONOS Y SEGUROS) -> titulo
                        'SERVICIOS PÚBLICOS',
                        'ABONO DE SERVICIOS',
                        'MANTENIMIENTO DE PARTES COMUNES',
                        'TRABAJO DE REPARACIONES EN UNIDADES',
                        'GASTOS DE LIMPIEZA',
                        'GASTOS BANCARIOS',
                        'GASTOS DE ADMINISTRACIÓN',
                        'SEGUROS ORDINARIOS',
                        'OTROS GASTOS ORDINARIOS',
                        # REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES -> titulo
                        'CARGAS SOCIALES',
                        'IMPUTACIONES DEL SUELDO',
                        # GASTOS PARTICULARES DEL PERÍODO' -> titulo
                        'PERÍODO GASTO',
                        'UNIDAD FUNCIONAL']

            all_sheets_values = []
            for sheet in total_sheets:
                sheet_name = sheet['properties']['title']
                result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
                values = result.get('values', [])
                for fila in values:
                    all_sheets_values.append(fila)

            # Encontrar el índice de la fila que contiene "Detalle de gastos, ingresos y saldos"
            indice_inicio = None
            indice_fin = None

            ######### modificar para considerar mas años ############
            texto_url_sheet = nombre_spreadsheet[:-8]
            anio =  nombre_spreadsheet[-7:-3]
            mes = nombre_spreadsheet[-2:]
            nro_sheets = 'rendicion-mes_' + anio + '-' + mes

            fila_comienzo_gastos = "Detalle de gastos, ingresos y saldos de " + numero_a_mes(mes) + " " + anio
            fila_fin_gastos = "RESUMEN DE INGRESOS Y EGRESOS"

            for i, fila in enumerate(all_sheets_values):
                if fila != []:
                    if fila_comienzo_gastos in fila[0]:
                        indice_inicio = i
                    elif fila_fin_gastos in fila[0].split("\n")[0].strip():
                        indice_fin = i
                        break

            # Si se encuentra el valor, eliminar todas las filas previas
            if indice_inicio is not None and indice_fin is not None:
                all_sheets_values = all_sheets_values[indice_inicio+1:indice_fin-1]

            lista_data_gastos = []
            empleado, largo_fila_encabezado, titulo, subtitulo, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None

            if all_sheets_values:       
                for fila in all_sheets_values:
                    # print('fila: ', fila)
                    cuit_o_cuil = ''
                    if fila != []:      
                        # print('fila: ', fila)          
                        if 'PERÍODO\nGASTO' in fila or 'UNIDAD\nFUNCIONAL' in fila:
                            # reemplazamos tanto PERIODO\nGASTO por PERIOD GASTO como tambien GASTO\nPARTICULAR, IMPORTE\nTOTAL 
                            # y SALDO\nIMPAGO por GASTO PARTICULAR, IMPORTE TOTAL y SALDO IMPAGO
                            fila = [item.replace('\n', ' ') for item in fila]
                        
                        lineas = [linea.strip() for linea in fila[0].split("\n")]
                        mas_lineas = [linea.strip() for linea in fila[1:] if '$' not in linea and linea != '']

                        if lineas != [] and mas_lineas != []:
                            lineas = [*lineas, *mas_lineas]

                        *variables, = lineas
                        fila_sin_newline = variables[0]

                        print('variables: ', variables)
                        
                        # Como 'fila_sin_newline' suele ser un titulo o subtitulo, lo sacamos de los detalles
                        if any('\n' in fila for fila in variables):
                            if len(variables) > 1:
                                detalle_1 = [' '.join(elemento.split("\n")) for elemento in variables[1:]]
                            else:
                                detalle_1 = [' '.join(elemento.split("\n")) for elemento in fila[1:]]
                            detalle_2 = " ".join([elem for elem in detalle_1 if elem and "$" not in elem])
                        else:
                            if len(variables) > 1:
                                detalle_2 =  " ".join(variables[1:])
                            else:
                                detalle_2 =  " ".join(fila[1:])

                        # print('variables: ', variables)

                        detalle_2 = detalle_2.strip()
                        detalle_sin_factura = ''
                        detalle_sin_liq = ''
                        detalles = ''

                        print('detalle_2: ', detalle_2)

                        if '[Fc.' in detalle_2:       
                            pattern_factura = r"\[Fc\. (A|B|C) \d{4}-\d{8}\]"
                            pattern_tipo_factura = r"\[Fc\. ([A-C])"
                            pattern_numero_factura = r"\d{4}-\d{8}"
                            
                            match_factura = re.search(pattern_factura, detalle_2)
                            match_numero_factura = re.search(pattern_numero_factura, detalle_2)
                            match_tipo_factura = re.search(pattern_tipo_factura, detalle_2)

                            if match_factura:
                                factura = match_factura.group(0)
                                numero_factura = match_numero_factura.group(0)
                                tipo_factura = match_tipo_factura.group(1)

                                if detalle_2.find(factura) == 0:
                                    detalle_sin_factura = detalle_2[detalle_2.find(factura) + len(factura) +1:].strip()
                                else:
                                    a = detalle_2[:detalle_2.find(factura)-1].strip()
                                    b = detalle_2[detalle_2.find(factura) + len(factura) + 1:].strip()
                                    detalle_sin_factura = a + ' ' + b
                            else:
                                pattern_factura_con_cuota = r"\[Fc\. (A|B|C) \d{4}-\d{8}\]"

                                match_factura_con_cuota = re.search(pattern_factura_con_cuota, detalle_2)
                                numero_factura = match_numero_factura.group(0)
                                tipo_factura = match_tipo_factura.group(0)

                                if match_factura_con_cuota:
                                    factura_con_cuota = match_factura_con_cuota.group(0)

                                    if detalle_2.find(factura_con_cuota) == 0:
                                        detalle_sin_factura = detalle_2[detalle_2.find(factura_con_cuota) + len(factura_con_cuota) +1:].strip()
                                    else:
                                        a = detalle_2[:detalle_2.find(factura_con_cuota)-1].strip()
                                        b = detalle_2[detalle_2.find(factura_con_cuota) + len(factura_con_cuota) + 1:].strip()
                                        detalle_sin_factura = a + ' ' + b

                                    print('detalle_sin_factura: ', detalle_sin_factura)

                        if '[Pago ' in detalle_sin_factura or (detalle_sin_factura == '' and '[Pago ' in detalle_2) or '[Pago ' in fila_sin_newline:  
                            
                            if '[Pago ' in fila_sin_newline:
                                detalle_sin_factura = fila_sin_newline
                                # print('detalle_sin_factura: ', detalle_sin_factura)

                            if detalle_sin_factura == '' and '[Pago ' in detalle_2:
                                detalle_sin_factura = detalle_2
                            
                            pattern_fecha_de_pago_con_op = r"\[?Pago (\d{2}/\d{2}/\d{2}) - OP\s*([\d]{4}\s*-\s*[\d]{8})\]?"
                            match_fecha_de_pago_con_op = re.search(pattern_fecha_de_pago_con_op, detalle_sin_factura)

                            pattern_fecha_de_pago = r"\[?Pago (\d{2}/\d{2}/\d{2})\]?"
                            match_fecha_de_pago = re.search(pattern_fecha_de_pago, detalle_sin_factura)
                            
                            if match_fecha_de_pago_con_op:
                                fecha_y_numero_de_pago = match_fecha_de_pago_con_op.group(0).strip()  # "11/09/23 - OP 0001-00001088"
                                fecha_de_pago_factura = match_fecha_de_pago_con_op.group(1).strip()  # "11/09/23"
                                orden_de_pago_factura = match_fecha_de_pago_con_op.group(2).strip()  # "0001-00001088"

                                if detalle_sin_factura.find(fecha_y_numero_de_pago) == 1:
                                    detalles = detalle_sin_factura[detalle_sin_factura.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) +1:].strip()
                                else:
                                    a = detalle_sin_factura[:detalle_sin_factura.find(fecha_y_numero_de_pago)-1].strip()
                                    b = detalle_sin_factura[detalle_sin_factura.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) + 1:].strip()
                                    detalles = a + ' ' + b

                                # print('detalle: ', detalles)

                            elif detalle_sin_factura[-1].isnumeric() == False and match_fecha_de_pago:

                                fecha_de_pago_factura = match_fecha_de_pago.group(0).strip()
                                pattern_recibo_y_fecha_de_pago = r"Recibo:\s*\d+\s*\[Pago\s*\d{2}/\d{2}/\d{2}\]"
                                match_recibo_y_fecha_de_pago = re.search(pattern_recibo_y_fecha_de_pago, detalle_sin_factura)

                                if match_recibo_y_fecha_de_pago: # solo aplica en remuneraciones creo
                                    recibo_y_fecha_de_pago = match_recibo_y_fecha_de_pago.group(0).strip()

                                    pattern_fecha_de_pago = r"\[?Pago (\d{2}/\d{2}/\d{2})\]?"
                                    match_fecha_de_pago = re.search(pattern_fecha_de_pago, detalle_sin_factura)

                                    if match_fecha_de_pago_con_op:
                                        fecha_y_numero_de_pago = match_fecha_de_pago_con_op.group(0).strip()  # "11/09/23 - OP 0001-00001088"
                                        fecha_de_pago_factura = match_fecha_de_pago_con_op.group(1).strip()  # "11/09/23"
                                        orden_de_pago_factura = match_fecha_de_pago_con_op.group(2).strip()  # "0001-00001088"

                                    for empleado in empleados_fijos:
                                        if empleado in variables[0]:
                                            proveedor = empleado
                                    
                                    if detalle_2 != '' and 'Cargo:' in detalle_2:
                                        if 'Recibo' in detalle_2:
                                            detalle_2 = detalle_2.strip('Cargo:').strip()
                                            if detalle_2.find(recibo_y_fecha_de_pago) == 0:
                                                detalles = detalle_2[detalle_2.find(recibo_y_fecha_de_pago) + len(recibo_y_fecha_de_pago) +1:].strip()
                                            else:
                                                a = detalle_2[:detalle_2.find(recibo_y_fecha_de_pago)-1].strip()
                                                b = detalle_2[detalle_2.find(recibo_y_fecha_de_pago) + len(recibo_y_fecha_de_pago) + 1:].strip()
                                                detalles = a + ' ' + b
                                        else:
                                            detalles = detalle_2.strip('Cargo:').strip()

                                    else:
                                        if detalle_sin_factura.find(recibo_y_fecha_de_pago) == 0:
                                            detalles = detalle_sin_factura[detalle_sin_factura.find(recibo_y_fecha_de_pago) + len(recibo_y_fecha_de_pago) +1:].strip()
                                        else:
                                            a = detalle_sin_factura[:detalle_sin_factura.find(recibo_y_fecha_de_pago)-1].strip()
                                            b = detalle_sin_factura[detalle_sin_factura.find(recibo_y_fecha_de_pago) + len(recibo_y_fecha_de_pago) + 1:].strip()
                                            detalles = a + ' ' + b
                                
                                elif detalle_sin_factura[-2:] == 'OP':
                                    
                                    pattern_orden_pago_cortada = r"\d{4}-\d{8}"
                                    match_numero_op = re.search(pattern_orden_pago_cortada, detalle_sin_factura)

                                    if match_numero_op:
                                        orden_de_pago_cortada = match_numero_op.group(0).strip()
                                
                                        if detalle_sin_factura.find(orden_de_pago_cortada) == 0:
                                            detalle_sin_factura_con_op = detalle_sin_factura[detalle_sin_factura.find(orden_de_pago_cortada) + len(orden_de_pago_cortada) +1:].strip()
                                        else:
                                            a = detalle_sin_factura[:detalle_sin_factura.find(orden_de_pago_cortada)-1].strip()
                                            b = detalle_sin_factura[detalle_sin_factura.find(orden_de_pago_cortada) + len(orden_de_pago_cortada) + 1:].strip()
                                            detalle_sin_factura_con_op = a + ' ' + b

                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op + ' ' + orden_de_pago_cortada + ']'
                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op.strip()

                                        pattern_fecha_de_pago_con_op = r"\[?Pago (\d{2}/\d{2}/\d{2}) - OP\s*([\d]{4}\s*-\s*[\d]{8})\]?"
                                        match_fecha_de_pago_con_op = re.search(pattern_fecha_de_pago_con_op, detalle_sin_factura_con_op)
                                        fecha_y_numero_de_pago = match_fecha_de_pago_con_op.group(0).strip()

                                        if match_fecha_de_pago_con_op:
                                            if detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) == 1:
                                                detalles = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) +1:].strip()
                                            else:
                                                a = detalle_sin_factura_con_op[:detalle_sin_factura_con_op.find(fecha_y_numero_de_pago)-1].strip()
                                                b = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) + 1:].strip()
                                                detalles = a + ' ' + b

                                # sirve cuando termina en "[Pago dd/mm/yyyy - OP dddd-" o en "[Pago dd/mm/yyyy -" (esto busca la parte final que quedo cortada, no la inicial)
                                elif detalle_sin_factura.strip()[-1] == '-':

                                    pattern_op = r"-?\s?OP (\d{4}-\d{8})"
                                    match = re.search(pattern_op, detalle_sin_factura)
                                    if match:
                                        op_match = match.group(0)
                                        orden_de_pago_cortada = re.sub(r"[^\d-]", "", match.group(0).strip())
                                        if orden_de_pago_cortada[0] == "-":
                                            orden_de_pago_cortada = orden_de_pago_cortada[1:]

                                        if detalle_sin_factura.find(op_match) == 1:
                                            detalle_sin_factura_con_op = detalle_sin_factura[detalle_sin_factura.find(op_match) + len(op_match) +1:].strip()
                                        else:
                                            a = detalle_sin_factura[:detalle_sin_factura.find(op_match)-1].strip()
                                            b = detalle_sin_factura[detalle_sin_factura.find(op_match) + len(op_match) + 1:].strip()
                                            detalle_sin_factura_con_op = a + ' ' + b

                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op + ' OP ' + orden_de_pago_cortada + ']'
                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op.strip()

                                    else:
                                        pattern_mitad_op = r"\d{8}\]"
                                        match_mitad = re.search(pattern_mitad_op, detalle_sin_factura)
                                        if match_mitad:
                                            mitad_op_match = match_mitad.group(0)
                                            mitad_op = mitad_op_match.strip("]")
                                            detalle_sin_factura = detalle_sin_factura + mitad_op + ']'
                                            if detalle_sin_factura.find(mitad_op_match) == 0:
                                                detalle_sin_factura_con_op = detalle_sin_factura[detalle_sin_factura.find(mitad_op_match) + len(mitad_op_match) +1:].strip()
                                            else:
                                                a = detalle_sin_factura[:detalle_sin_factura.find(mitad_op_match)-1].strip()
                                                b = detalle_sin_factura[detalle_sin_factura.find(mitad_op_match) + len(mitad_op_match) + 1:].strip()
                                                detalle_sin_factura_con_op = (a + ' ' + b).strip()
                                            
                                    pattern_fecha_de_pago_con_op = r"\[?Pago (\d{2}/\d{2}/\d{2}) - OP\s*([\d]{4}\s*-\s*[\d]{8})\]?"
                                    match_fecha_de_pago_con_op = re.search(pattern_fecha_de_pago_con_op, detalle_sin_factura_con_op)

                                    fecha_y_numero_de_pago = match_fecha_de_pago_con_op.group(0).strip()  # "11/09/23 - OP 0001-00001088"
                                    fecha_de_pago_factura = match_fecha_de_pago_con_op.group(1).strip()  # "11/09/23"
                                    orden_de_pago_factura = match_fecha_de_pago_con_op.group(2).strip()  # "0001-00001088"

                                    if detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) == 1:
                                        detalles = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) +1:].strip()
                                    else:
                                        a = detalle_sin_factura_con_op[:detalle_sin_factura_con_op.find(fecha_y_numero_de_pago)-1].strip()
                                        b = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) + 1:].strip()
                                        detalles = a + ' ' + b

                                else:

                                    if detalle_sin_factura.find(fecha_de_pago_factura) == 0:
                                        detalles = detalle_sin_factura[detalle_sin_factura.find(fecha_de_pago_factura) + len(fecha_de_pago_factura) +1:].strip()
                                    else:

                                        a = detalle_sin_factura[:detalle_sin_factura.find(fecha_de_pago_factura)-1].strip()
                                        b = detalle_sin_factura[detalle_sin_factura.find(fecha_de_pago_factura) + len(fecha_de_pago_factura) + 1:].strip()
                                        detalles = a + ' ' + b
                                    
                                    fecha_de_pago_factura = fecha_de_pago_factura.strip("[").strip("]").strip()

                                fecha_de_pago_factura = fecha_de_pago_factura.strip("[Pago ").strip("]").strip()

                            # Si la orden de pago y fecha de pago salen cortadas
                            else:            
                                # primero buscamos si esta cortado tipo 'OP - dddd-dddddddd' porque si buscamos de una por dddd-ddddddd
                                # puede que nos matchee con el numero de LSP antes que la OP
                                pattern_op = r"-?\s?OP (\d{4}-\d{8})"
                                match = re.search(pattern_op, detalle_sin_factura)
                                op_match = match.group(0)
                            
                                if match:
                                    orden_de_pago_cortada = re.sub(r"[^\d-]", "", match.group(0).strip())
                                    if orden_de_pago_cortada[0] == "-":
                                        orden_de_pago_cortada = orden_de_pago_cortada[1:]

                                    if detalle_sin_factura.find(op_match) == 1:
                                        detalle_sin_factura_con_op = detalle_sin_factura[detalle_sin_factura.find(op_match) + len(op_match) +1:].strip()
                                    else:
                                        a = detalle_sin_factura[:detalle_sin_factura.find(op_match)-1].strip()
                                        b = detalle_sin_factura[detalle_sin_factura.find(op_match) + len(op_match) + 1:].strip()
                                        detalle_sin_factura_con_op = a + ' ' + b

                                    detalle_sin_factura_con_op = detalle_sin_factura_con_op + ' - OP ' + orden_de_pago_cortada + ']'
                                    detalle_sin_factura_con_op = detalle_sin_factura_con_op.strip()

                                    pattern_fecha_de_pago_con_op = r"\[?Pago (\d{2}/\d{2}/\d{2}) - OP\s*([\d]{4}\s*-\s*[\d]{8})\]?"
                                    match_fecha_de_pago_con_op = re.search(pattern_fecha_de_pago_con_op, detalle_sin_factura_con_op)

                                    fecha_y_numero_de_pago = match_fecha_de_pago_con_op.group(0).strip()  # "11/09/23 - OP 0001-00001088"
                                    fecha_de_pago_factura = match_fecha_de_pago_con_op.group(1).strip()  # "11/09/23"
                                    orden_de_pago_factura = match_fecha_de_pago_con_op.group(2).strip()  # "0001-00001088"

                                    if detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) == 1:
                                        detalles = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) +1:].strip()
                                    else:
                                        a = detalle_sin_factura_con_op[:detalle_sin_factura_con_op.find(fecha_y_numero_de_pago)-1].strip()
                                        b = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) + 1:].strip()
                                        detalles = a + ' ' + b

                                else:
                                    pattern_orden_pago_cortada = r"\d{4}-\d{8}"
                                    match = re.search(pattern_orden_pago_cortada, detalle_sin_factura)

                                    if match:
                                        orden_de_pago_cortada = match.group(0).strip()
                                
                                        if detalle_sin_factura.find(orden_de_pago_cortada) == 1:
                                            detalle_sin_factura_con_op = detalle_sin_factura[detalle_sin_factura.find(orden_de_pago_cortada) + len(orden_de_pago_cortada) +1:].strip()
                                        else:
                                            a = detalle_sin_factura[:detalle_sin_factura.find(orden_de_pago_cortada)-1].strip()
                                            b = detalle_sin_factura[detalle_sin_factura.find(orden_de_pago_cortada) + len(orden_de_pago_cortada) + 1:].strip()
                                            detalle_sin_factura_con_op = a + ' ' + b

                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op + ' ' + orden_de_pago_cortada + ']'
                                        detalle_sin_factura_con_op = detalle_sin_factura_con_op.strip()

                                        if detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) == 1:
                                            detalles = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) +1:].strip()
                                        else:
                                            a = detalle_sin_factura_con_op[:detalle_sin_factura_con_op.find(fecha_y_numero_de_pago)-1].strip()
                                            b = detalle_sin_factura_con_op[detalle_sin_factura_con_op.find(fecha_y_numero_de_pago) + len(fecha_y_numero_de_pago) + 1:].strip()
                                            detalles = a + ' ' + b
                        
                        if detalles != '' and '[LSP ' in detalles: # Liquidacion servicio publico    
                            pattern_liq = r"\[LSP\ (A|B|C) \d{4}-\d{8}\]"
                            pattern_tipo_liq = r"\A|B|C"
                            pattern_numero_liq = r"\d{4}-\d{8}"
                            
                            liquidacion = re.search(pattern_liq, detalles).group(0)
                            tipo_liq = re.search(pattern_tipo_liq, detalles).group(0)
                            numero_liq = re.search(pattern_numero_liq, detalles).group(0)

                            if detalles.find(liquidacion) == 0:
                                detalle_sin_liq = detalles[detalles.find(liquidacion) + len(liquidacion) +1:].strip()
                            else:
                                a = detalles[:detalles.find(liquidacion)-1].strip()
                                b = detalles[detalles.find(liquidacion) + len(liquidacion) + 1:].strip()
                                detalle_sin_liq = a + ' ' + b
                        
                        if detalle_sin_factura != '' and detalles == '' and detalle_sin_liq == '':
                            detalles = detalle_sin_factura

                        elif detalle_sin_factura != '' and detalles != '' and detalle_sin_liq == '':
                            pass #dejamos detalles como detalles (resultado del if de 'Pago')

                        elif detalle_sin_liq != '': # con esta condicion sola ya implica que detalle_sin_factura != '' and detalles != '', es el ultimo cascadeo de ifs
                            detalles = detalle_sin_liq

                        else:
                            detalles = list(filter(lambda x: x != "", fila[1:])) if len(fila[1:]) > 0 else ""
                            if subtitulo not in ['PERÍODO GASTO','UNIDAD FUNCIONAL']:
                                detalles = list(filter(lambda x: '$' not in x, detalles)) if len(detalles) > 0 else ""

                        # print('detalles: ', detalles)

                        if fila_sin_newline in titulos or fila_sin_newline.startswith("GASTOS DEVENGADOS EN MESES ANTERIORES PAGADOS EN"):
                            titulo = fila_sin_newline
                        elif fila_sin_newline in subtitulos:
                            encabezados, subtitulo = fila, fila_sin_newline
                            largo_fila_encabezado = len(encabezados)
                            if subtitulo == 'PERÍOD GASTO':
                                ultima_columna = 'MONTO PAGO' # es la segunda version de gastos particulares: ['PERIODO GASTO','PROVEEDOR','COMPROBANTE GASTO','IMPORTE TOTAL GASTO', 'FECHA PAGO', 'ORDEN PAGO', 'MONTO PAGO']
                            else:
                                ultima_columna = 'SALDO IMPAGO'
                        elif titulo == 'REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES' or (any('TOTAL' in item.upper() for item in fila) == False and any('SUBTOTAL' in item.upper() for item in fila) == False):
                            if any('$' in item for item in fila) or titulo == 'REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES':
                                if subtitulo == 'PERÍODO GASTO':
                                    ##### Gastos Devengados en Meses Anteriores pagados en el mes actual #####
                                    # el formato cambia en una fecha especifica de tener columnas
                                    # periodo gasto, proveedor, comprobante, cuenta, improte total, saldo impago ==>>
                                    # periodo gasto, proveedor, comprobante gasto, importe total gasto, fecha pago, orden pago, monto pago
                                    # en cantidad de celdas ocupan lo mismo pero ahora estan agrupadas distintas las celdas en estas diferentes columnas
                                    # lo podemos chequear con la ultima columna

                                    if ultima_columna == 'MONTO PAGO':
                                        proveedor = detalles[0]
                                        comprobante = detalles[1]
                                        periodo_gasto = fila[0]
                                        saldo_impago = detalles[2]
                                        saldo_impago = saldo_impago[saldo_impago.find("$")+1:].strip()
                                        fecha_de_pago = detalles[3]
                                        orden_de_pago = detalles[4]

                                    else:
                                        proveedor = detalles[0] # es tipo LUSON SEGURIDAD
                                        comprobante = detalles[1] # es tipo '0002-000000992'
                                        cuenta = detalles[2].upper() # es como un subtitulo que dice Abono de Servicios => ponerlo en otra columna tipo
                                        # categoria_pago_devengado y en la columna subtitulo dejar en blanco (borrar el PERIODO GASTO)
                                        periodo_gasto = fila[0] # es tipo 'Ago. 2023'
                                        montos = [item.strip() for item in detalles if "$" in item]
                                        saldo_impago = [item.strip() for item in detalles if "$" in item][0]
                                        saldo_impago = saldo_impago[saldo_impago.find("$")+1:]

                                    detalles = ''

                                    lista_data_gastos, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = cargar_datos_df(gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura)
                                elif subtitulo == 'UNIDAD FUNCIONAL':
                                    uf = fila[0] # es tipo 3-05

                                    if 'CUIL:' in detalles:
                                        match = re.search(r"CUIL:\s*(\d{2}-\d{8}-\d)", detalles)
                                        cuil = match.group(0)
                                        numero_cuil = cuil.strip("CUIL: ").strip()
                                        if detalles.find(cuil) == 0:
                                            detalles = detalles[detalles.find(cuil) + len(cuil) +1:].strip()
                                        else:
                                            proveedor = detalles[:detalles.find(cuil)-1].strip()
                                            detalles = detalles[detalles.find(cuil) + len(cuil) + 1:].strip()
                                    elif 'CUIT ' in detalles:
                                        match = re.search(r"CUIT\s*(\d{2}-\d{8}-\d)", detalles)
                                        cuit = match.group(0)
                                        numero_cuit = cuit.strip("[CUIT ").strip("]").strip()
                                        if detalles.find(cuit) == 0:
                                            detalles = detalles[detalles.find(cuit) + len(cuit) +1:].strip()
                                        else:
                                            proveedor = detalles[:detalles.find(cuit)-1].strip()
                                            detalles = detalles[detalles.find(cuit) + len(cuit) + 1:].strip()
                                    else:
                                        proveedor = detalles[0]
                                                                
                                    if any('$' in item for item in detalles):
                                        detalles = [linea.strip() for linea in detalles if '$' not in linea and linea != proveedor and linea != '']
                                        detalles = ' '.join(detalles).strip()
                                        
                                    gasto_particular = [item.strip() for item in fila if "$" in item]
                                    if gasto_particular != []:
                                        gasto_particular = gasto_particular[0]
                                        gasto_particular = gasto_particular[gasto_particular.find("$")+1:].strip()

                                    lista_data_gastos, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = cargar_datos_df(gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura)    
                                else:
                                    if titulo == 'REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES' and any('TOTAL' in item.upper() for item in fila) == False and any('SUBTOTAL' in item.upper() for item in fila) == False:                     
                                        if len(variables) > 1 and (detalles == '' or detalles == []):
                                            detalles = ' '.join(variables[1:])
                                        elif detalles != '' or detalles != []:
                                            pass # dejamos detalles como esta
                                        else:
                                            detalles = ''

                                        if 'CUIL:' in fila_sin_newline:
                                            match = re.search(r"CUIL:\s*(\d{2}-\d{8}-\d)", fila_sin_newline)
                                            cuil = match.group(0)
                                            numero_cuil = cuil.strip("CUIL: ").strip()
                                            
                                            if proveedor == '':
                                                if fila_sin_newline.find(cuil) == 0:
                                                    proveedor = fila_sin_newline[fila_sin_newline.find(cuil) + len(cuil) +1:].strip()
                                                else:
                                                    a = fila_sin_newline[:fila_sin_newline.find(cuil)-1].strip()
                                                    b = fila_sin_newline[fila_sin_newline.find(cuil) + len(cuil) + 1:].strip()
                                                    proveedor = a + ' ' + b

                                        elif 'CUIT ' in fila_sin_newline:
                                            match = re.search(r"CUIT\s*(\d{2}-\d{8}-\d)", fila_sin_newline)
                                            cuit = match.group(0)
                                            numero_cuit = cuit.strip("[CUIT ").strip("]").strip()

                                            if proveedor is None or proveedor == '':
                                                if fila_sin_newline.find(cuit) == 0:
                                                    proveedor = fila_sin_newline[fila_sin_newline.find(cuit) + len(cuit) +1:].strip()
                                                else:
                                                    a = fila_sin_newline[:fila_sin_newline.find(cuit)-1].strip()
                                                    b = fila_sin_newline[fila_sin_newline.find(cuit) + len(cuit) + 1:].strip()
                                                    proveedor = a + ' ' + b

                                        elif 'CUIL:' in detalles:
                                            match = re.search(r"CUIL:\s*(\d{2}-\d{8}-\d)", detalles)
                                            cuil = match.group(0)
                                            numero_cuil = cuil.strip("CUIL: ").strip()

                                            if detalles.find(cuil) == 0:
                                                detalles = detalles[detalles.find(cuil) + len(cuil) +1:].strip()
                                            else:
                                                a = detalles[:detalles.find(cuil)-1].strip()
                                                b = detalles[detalles.find(cuil) + len(cuil) + 1:].strip()
                                                detalles = a + ' ' + b

                                        elif 'CUIT ' in detalles:
                                            match = re.search(r"CUIT\s*(\d{2}-\d{8}-\d)", detalles)
                                            cuit = match.group(0)
                                            numero_cuit = cuit.strip("[CUIT ").strip("]").strip()

                                            if detalles.find(cuit) == 0:
                                                detalles = detalles[detalles.find(cuit) + len(cuit) +1:].strip()
                                            else:
                                                a = detalles[:detalles.find(cuit)-1].strip()
                                                b = detalles[detalles.find(cuit) + len(cuit) + 1:].strip()
                                                detalles = a + ' ' + b

                                        if any('$' in item for item in fila): #Los sueldos siempre pasan solo como Gasto Comun
                                            montos = [item.strip() for item in fila if "$" in item]
                                            gasto_comun = montos[0]
                                            gasto_comun = gasto_comun[gasto_comun.find("$")+1:].strip()

                                        lista_data_gastos, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = cargar_datos_df(gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura)
                                    elif any('TOTAL' in item.upper() for item in variables) == False and any('SUBTOTAL' in item.upper() for item in variables) == False:
                                                                        
                                        montos = [item.strip() for item in fila if "$" in item]

                                        if len(montos) > 1:
                                            gasto_vivienda = montos[1]
                                            gasto_vivienda = gasto_vivienda[gasto_vivienda.find("$")+1:]
                                            gasto_comun = montos[0]
                                            gasto_comun = gasto_comun[gasto_comun.find("$")+1:]
                                        elif len(fila) == largo_fila_encabezado: # len(montos) = 1 => o gasto viviendo o gasto comun
                                            gasto_vivienda = montos[0][montos[0].find("$")+1:]
                                        else: # es gasto comun 
                                            gasto_comun = montos[0]
                                            gasto_comun = gasto_comun[gasto_comun.find("$")+1:]
                                        
                                        # Proveedor, numero cuit o cuil, descripciones del gasto
                                        if 'CUIL:' in fila_sin_newline:
                                            match = re.search(r"CUIL:\s*(\d{2}-\d{8}-\d)", fila_sin_newline)
                                            numero_cuil = match.group(1)
                                            proveedor = fila_sin_newline[:fila_sin_newline.find('CUIL:')]
                                        elif 'CUIT ' in fila_sin_newline:
                                            match = re.search(r"CUIT\s*(\d{2}-\d{8}-\d)", fila_sin_newline)
                                            numero_cuit = match.group(1)
                                            numero_cuit.strip("[").strip("]")
                                            proveedor = fila_sin_newline[:fila_sin_newline.find('[CUIT ')]
                                        elif 'CUIL:' in detalles:
                                            match = re.search(r"CUIL:\s*(\d{2}-\d{8}-\d)", detalles)
                                            cuil = match.group(0)
                                            numero_cuil = cuil.strip('CUIL:').strip()

                                            if detalles.find(cuil) == 0:
                                                detalles = detalles[detalles.find(cuil) + len(cuil) +1:].strip()
                                            else:
                                                a = detalles[:detalles.find(cuil)-1].strip()
                                                b = detalles[detalles.find(cuil) + len(cuil) + 1:].strip()
                                                detalles = a + ' ' + b

                                            proveedor = fila_sin_newline
                                        elif 'CUIT ' in detalles:
                                            match = re.search(r"CUIT\s*(\d{2}-\d{8}-\d)", detalles)
                                            cuit = match.group(0)
                                            numero_cuit = cuit.strip("[CUIT").strip("]").strip()

                                            if detalles.find(cuit) == 0:
                                                detalles = detalles[detalles.find(cuit) + len(cuit) +1:].strip()
                                            else:
                                                a = detalles[:detalles.find(cuit)-1].strip()
                                                b = detalles[detalles.find(cuit) + len(cuit) + 1:].strip()
                                                detalles = a + ' ' + b

                                            proveedor = fila_sin_newline
                                        else:
                                            proveedor = fila_sin_newline

                                        indice = next((i for i, elem in enumerate(detalles) if 'CUIT' in elem or 'CUIL' in elem), None)
                                        resultado = next((elem for elem in detalles[indice + 1:] if elem.strip()), "") if indice is not None else ""

                                        if resultado != "":
                                            if isinstance(resultado, list):
                                                if any('\n' in item for item in resultado):
                                                    resultado = [linea.replace("\n"," ") for linea in resultado]
                                                    resultado_unico = " ".join(resultado)
                                                else:
                                                    resultado_unico = " ".join(resultado)
                                            elif '\n' in resultado:
                                                resultado_unico = resultado.replace("\n"," ")
                                            else:
                                                detalles = resultado
                                        elif isinstance(detalles, list) and len(detalles) > 1:
                                            resultado = [linea.replace("\n"," ") for linea in detalles]
                                            resultado_unico = " ".join(resultado)
                                            detalles = resultado_unico

                                        if isinstance(detalles, list) and detalles != []:
                                            detalles = detalles[0]
                                        else:
                                            pass # dejamos detalles como esta

                                        if isinstance(detalles, list):
                                            if any('Fc.' in e for e in detalles):
                                                indice = next((i for i, elem in enumerate(detalles) if 'Fc.' in elem), None)
                                                detalles = next((elem for elem in detalles[indice + 1:] if elem.strip()), "") if indice is not None else ""
                                            elif any('LSP' in e for e in detalles):
                                                indice = next((i for i, elem in enumerate(detalles) if 'LSP' in elem), None)
                                                detalles = next((elem for elem in detalles[indice + 1:] if elem.strip()), "") if indice is not None else ""                               
                                            elif any('CUIT' in e for e in detalles):
                                                indice = next((i for i, elem in enumerate(detalles) if 'CUIT' in elem), None)
                                                detalles = next((elem for elem in detalles[indice + 1:] if elem.strip()), "") if indice is not None else ""                               
                                            elif any('CUIL' in e for e in detalles):
                                                indice = next((i for i, elem in enumerate(detalles) if 'CUIL' in elem), None)
                                                detalles = next((elem for elem in detalles[indice + 1:] if elem.strip()), "") if indice is not None else ""                               
                                        else: # no es lista
                                            pass
                                        
                                        if gasto_comun is not None:
                                            gasto_comun = gasto_comun.strip()
                                        if gasto_vivienda is not None:
                                            gasto_vivienda = gasto_vivienda.strip()
                                        if detalles != '' or detalles != []:
                                            pass
                                            # detalles = detalles.strip()

                                        lista_data_gastos, gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura = cargar_datos_df(gasto_comun, gasto_vivienda, proveedor, numero_cuit, numero_cuil, saldo_impago, periodo_gasto, cuenta, comprobante, uf, gasto_particular, detalles, tipo_factura, numero_factura, fecha_de_pago_factura, orden_de_pago_factura)
                        else:
                            pass
                            
                df_gastos = pd.DataFrame(lista_data_gastos)

                # Crear una columna para identificar grupos basados en 'columna1'
                df_gastos['group_id'] = df_gastos['subtitulo'].notna().cumsum()

                # Combinar valores no nulos en cada grupo
                df_grouped = df_gastos.groupby('group_id').agg(lambda x: ' '.join(map(str, x.dropna())))

                # Eliminar la columna de agrupación
                df_grouped = df_grouped.reset_index(drop=True)
                df_grouped.loc[df_grouped['titulo'] == 'GASTOS DEVENGADOS PENDIENTES DE PAGO (CUENTAS POR PAGAR)', 'subtitulo'] = ''
                df_grouped.loc[df_grouped['titulo'] == 'GASTOS DEVENGADOS PENDIENTES DE PAGO (CUENTAS POR PAGAR)', 'detalles'] = ''

                idx = df_grouped[df_grouped["titulo"] == "REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES"].index.min()
                if pd.notna(idx):  
                    df_grouped.at[idx, "subtitulo"] = "IMPUTACIONES DEL SUELDO"
            
                # Convertimos los valores vacíos en NaN
                df_grouped.replace("", None, inplace=True)

                # Filtro para aplicar la transformación solo a las filas indicadas
                mask = (df_grouped["titulo"] == "REMUNERACIONES AL PERSONAL Y CARGAS SOCIALES") & (df_grouped["subtitulo"] == "IMPUTACIONES DEL SUELDO")

                # Copiar valores de gasto_comun en la fila anterior si está vacío
                for i in range(1, len(df_grouped)):
                    if mask[i] and pd.isna(df_grouped.loc[i-1, "gasto_comun"]) and not pd.isna(df_grouped.loc[i, "gasto_comun"]):
                        df_grouped.loc[i-1, "gasto_comun"] = df_grouped.loc[i, "gasto_comun"]

                # Eliminar filas donde "detalles" sea "[]", pero solo en las filas filtradas
                df_grouped = df_grouped[~(mask & (df_grouped["detalles"] == "[]"))].reset_index(drop=True)
                
            df_list.append(df_grouped)
                # cont += 1

if df_list:   
    # Concatenar todos los DataFrames
    combined_df = pd.concat(df_list, ignore_index=True)

    # Convertir DataFrame a lista de listas
    data = combined_df.values.tolist()
    if start_row == 1:
        data_headers = combined_df.columns.tolist()
        data.insert(0, data_headers)

    # Preparar el rango donde se agregará la nueva data
    range_to_update = f'{destination_sheet_name}!A{start_row}'

    # Escribir los datos en el Spreadsheet de destino
    body = {
        'values': data
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=destination_spreadsheet_id,
        range=range_to_update,
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f'Datos agregados al spreadsheet de destino en la hoja {destination_sheet_name}, comenzando desde la fila {start_row}.')
else:
    print('No hay nuevos datos para agregar.')
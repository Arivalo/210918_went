import requests
from czujnik import *
from system import SystemDiagnozy


def diagnostyka_tramwaje(data_od="2021-07-01", data_do="2021-07-03", nazwa_pliku="wyniki_diagnozy"):
    def pobierz_dane(url, haslo="Y9XrnmeE6d", login='wysocki;2177'):
        '''
        Pobiera dane z serwera Xtrack wedlug danego linku "url" i wyznacza kolumny z danymi GPS

        Wartosci wejsciowe:

        url <String> - pelny link z zapytaniem
        haslo <String> - haslo do autentykacji BASIC
        login <String> - (default: "wysocki;2139") login do autentykacji BASIC

        Wyjscie:

        <pandas.DataFrame> - otrzymany z zapytania DataFrame z danymi

        '''

        r = requests.get(url, auth=(login, haslo))

        j = r.json()

        df = pd.DataFrame.from_dict(j['entities'])
        if not df.empty:
            try:
                df['longtitude'] = [x['coordinates']['x'] for x in df['_meta']]
                df['latitude'] = [y['coordinates']['y'] for y in df['_meta']]
                df.pop('_meta')
            except KeyError:
                print(f'Problem z url: {url}')

        return df

    def get_predkosc_wozek_naped(Series, wozek='wozek_1'):

        def hex_2_bajt0(x):
            return ('00000000' + hex(x).split('x')[-1])[-8:][6:]

        def hex_2_bajt1(x):
            return ('00000000' + hex(x).split('x')[-1])[-8:][4:6]

        def add_0_1(x):
            hex_0 = hex_2_bajt0(x)
            hex_1 = hex_2_bajt1(x)
            hex_01 = hex_1 + hex_0
            return hex_01

        def hex_2_bajt2(x):
            return ('00000000' + hex(x).split('x')[-1])[-8:][2:4]

        def hex_2_bajt3(x):
            return ('00000000' + hex(x).split('x')[-1])[-8:][:2]

        def add_2_3(x):
            hex_2 = hex_2_bajt2(x)
            hex_3 = hex_2_bajt3(x)
            hex_23 = hex_3 + hex_2
            return hex_23

        nan_index = Series.isna().values
        nonan_index = ~nan_index
        predkosc_series = Series.copy()
        if sum(nonan_index) > 0:
            if wozek == 'wozek_1':
                vhex = np.vectorize(add_0_1)
            elif wozek == 'wozek_4':
                vhex = np.vectorize(add_2_3)

            hex_array = vhex(Series[nonan_index].astype('int').values)

            predkosc = [int(value, 16) / 100 for value in hex_array]
            predkosc_series[nonan_index] = predkosc
        else:
            pass

        return predkosc_series


    url_base = "https://2177.xtrack.com/rest/api/source-sets/archive-events"

    url_date_from = f"?from={data_od}T00:00:00Z"
    url_date_to = f"&to={data_do}T23:59:59Z"

    url_suffix = "&monitoredId=1&limit=10000000"

    url = url_base + url_date_from + url_date_to + url_suffix

    # identyczna z rename w skrypcie agregującym
    tabela_nazw = {
        # czujniki temperatury:
        'XT_UCAN_U16_008': 'temp_w1_przod_lewy',
        'XT_UCAN_U16_009': 'temp_w1_przod_prawy',
        'XT_UCAN_U16_010': 'temp_w1_tyl_lewy',
        'XT_UCAN_U16_011': 'temp_w1_tyl_prawy',

        'XT_UCAN_U16_048': 'temp_w2_przod_lewy',
        'XT_UCAN_U16_049': 'temp_w2_przod_prawy',
        'XT_UCAN_U16_050': 'temp_w2_tyl_lewy',
        'XT_UCAN_U16_051': 'temp_w2_tyl_prawy',

        'XT_UCAN_U16_072': 'temp_w3_przod_lewy',
        'XT_UCAN_U16_073': 'temp_w3_przod_prawy',
        'XT_UCAN_U16_074': 'temp_w3_tyl_lewy',
        'XT_UCAN_U16_075': 'temp_w3_tyl_prawy',

        'XT_UCAN_U16_092': 'temp_w4_przod_lewy',
        'XT_UCAN_U16_093': 'temp_w4_przod_prawy',
        'XT_UCAN_U16_094': 'temp_w4_tyl_lewy',
        'XT_UCAN_U16_095': 'temp_w4_tyl_prawy',

        # czujniki zawieszenia:
        'XT_UCAN_U16_005': 'zaw_w1_lewy',
        'XT_UCAN_U16_007': 'zaw_w1_prawy',

        'XT_UCAN_U16_045': 'zaw_w2_lewy',
        'XT_UCAN_U16_047': 'zaw_w2_prawy',

        'XT_UCAN_U16_069': 'zaw_w3_lewy',
        'XT_UCAN_U16_071': 'zaw_w3_prawy',

        'XT_UCAN_U16_089': 'zaw_w4_lewy',
        'XT_UCAN_U16_091': 'zaw_w4_prawy',

        # mikrofony:
        'XT_UCAN_U16_025': 'mikrofon_przekladnia_A',
        'XT_UCAN_U16_107': 'mikrofon_przekladnia_D',

        # chlodzenie:
        'XT_UCAN_U16_027': 'cisn_chlodzenie_silnika_A',
        'XT_UCAN_U16_111': 'cisn_chlodzenie_silnika_D',

        # temperatury:
        'XT_UCAN_U16_028': 'temp_otoczenia_A',
        'XT_UCAN_U16_112': 'temp_otoczenia_D',
        'XT_UCAN_U16_029': 'temp_chlodzenia_silnika_A',
        'XT_UCAN_U16_113': 'temp_chlodzenia_silnika_D',
        'XT_UCAN_U16_031': 'temp_przekladnia_A_1',
        'XT_UCAN_U16_030': 'temp_przekladnia_A_2',
        'XT_UCAN_U16_114': 'temp_przekladnia_D_1',
        'XT_UCAN_U16_115': 'temp_przekladnia_D_2',

        # akcelerometr
        'XT_UCAN_I16_020': 'rms_X_A_1',
        'XT_UCAN_I16_021': 'rms_Y_A_1',
        'XT_UCAN_I16_022': 'rms_Z_A_1',
        'XT_UCAN_I16_024': 'rms_X_A_2',
        'XT_UCAN_I16_025': 'rms_Y_A_2',
        'XT_UCAN_I16_026': 'rms_Z_A_2',
        'XT_UCAN_I16_104': 'rms_X_D_1',
        'XT_UCAN_I16_105': 'rms_Y_D_1',
        'XT_UCAN_I16_106': 'rms_Z_D_1',
        'XT_UCAN_I16_108': 'rms_X_D_2',
        'XT_UCAN_I16_109': 'rms_Y_D_2',
        'XT_UCAN_I16_110': 'rms_Z_D_2',
        # 'XT_UCAN_I16_023': 'akcelerometr_diagno_A',
        # 'XT_UCAN_I16_107': 'akcelerometr_diagno_D',

        # hamulce:
        'XT_UCAN_U16_001': 'cisnienie_hamulca_A',
        'XT_UCAN_U16_085': 'cisnienie_hamulca_D',

        # informacje z CANa:
        'XT_UCAN_U32_000': 'hamowanie_elektrod_kierunek_jazdy',
        'XT_UCAN_U32_001': 'zluzowane_hamulce_tarczowe',
        'XT_UCAN_U32_003': 'predkosc_osi',
        'XT_UCAN_U32_002': 'napiecie_i_prad_tramwaju',
        'XT_UCAN_I32_000': 'moment_zadany_A',
        'XT_UCAN_I32_008': 'moment_zadany_D',

        'XT_UCAN_I32_004': 'temp_falownika_i_silnika_A',
        'XT_UCAN_I32_005': 'wentylatory_i_obroty_silnika_A',
        'XT_UCAN_I32_014': 'temp_falownika_i_silnika_D',
        'XT_UCAN_I32_015': 'wentylatory_i_obroty_silnika_D',
        'XT_UCAN_I32_002': 'predkosc_falownika_i_mom_real_A',
        'XT_UCAN_I32_010': 'predkosc_falownika_i_mom_real_D',
        'XT_UCAN_I32_006': 'prad_wejciowy_i_czopera_A',
        'XT_UCAN_I32_012': 'prad_wejciowy_i_czopera_D',
        'XT_UCAN_I32_007': 'napiecia_wejsciowe_i_posredniczace_A',
        'XT_UCAN_I32_013': 'napiecia_wejsciowe_i_posredniczace_D',
    }

    odwrotna_tabela_nazw = {nazwa: xt for xt, nazwa in tabela_nazw.items()}

    kolumny_czujnikami_temp = ['temp_w1_przod_lewy', 'temp_w1_przod_prawy', 'temp_w1_tyl_lewy', 'temp_w1_tyl_prawy',
                               'temp_w2_przod_lewy', 'temp_w2_przod_prawy', 'temp_w2_tyl_lewy', 'temp_w2_tyl_prawy',
                               'temp_w3_przod_lewy', 'temp_w3_przod_prawy', 'temp_w3_tyl_lewy', 'temp_w3_tyl_prawy',
                               'temp_w4_przod_lewy', 'temp_w4_przod_prawy', 'temp_w4_tyl_lewy', 'temp_w4_tyl_prawy',
                               # 'temp_otoczenia_A','temp_otoczenia_D',
                               'temp_przekladnia_A_1', 'temp_przekladnia_A_2',
                               'temp_przekladnia_D_1', 'temp_przekladnia_D_2',
                               'temp_chlodzenia_silnika_A',
                               'temp_chlodzenia_silnika_D'
                               ]

    kolumny_z_czujnikami_zaw_naped = ['zaw_w1_lewy', 'zaw_w1_prawy', 'zaw_w4_lewy', 'zaw_w4_prawy']
    kolumny_z_czujnikami_zaw_toczne = ['zaw_w2_lewy', 'zaw_w2_prawy', 'zaw_w3_lewy', 'zaw_w3_prawy']

    zawieszenie_kalibracja_naped = [18.3, 11.7, 22.7, 19.2]
    zawieszenie_kalibracja_toczne = [30.2, 12.8, 32.7, 5.2]

    kolumny_z_czujnikami_hamulcow = ['cisnienie_hamulca_A', 'cisnienie_hamulca_D']

    kolumny_z_akcelerometrami = ['rms_X_A_1', 'rms_Y_A_1', 'rms_Z_A_1',
                                 'rms_X_A_2', 'rms_Y_A_2', 'rms_Z_A_2',
                                 'rms_X_D_1', 'rms_Y_D_1', 'rms_Z_D_1',
                                 'rms_X_D_2', 'rms_Y_D_2', 'rms_Z_D_2']

    kolumny_silnik_falownik = ['temp_falownika_i_silnika_A',
                               'temp_falownika_i_silnika_D']

    nazwy_silnik_falownik = [("temp_silnika_A", "temp_falownika_A"),
                             ("temp_silnika_D", "temp_falownika_D")]

    # -----------------------------------------------------------------------------------------------------------#
    # -----------------------------------------------------------------------------------------------------------#

    dane_df = pobierz_dane(url)
    dane_df.ffill(inplace=True)

    seria_dt = pd.to_datetime(dane_df['updatedAt'])
    seria_predkosc = get_predkosc_wozek_naped(dane_df[odwrotna_tabela_nazw['predkosc_osi']])

    diagnostyka = SystemDiagnozy(nazwa_pliku=nazwa_pliku)
    # czujniki temperatury
    for czujnik_temp in kolumny_czujnikami_temp:
        try:
            diagnostyka.dodaj_czujnik(CzujnikTemperaturyLozysk(dane_df[odwrotna_tabela_nazw[czujnik_temp]],
                                                               nazwa=czujnik_temp,
                                                               dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikTemperaturyLozysk(None,
                                                               nazwa=czujnik_temp))
            print(f"Brak danych czujnika: {czujnik_temp}")

    # czujniki zawieszenia
    # napedowe
    for czujnik_zaw_naped, kalibracja in zip(kolumny_z_czujnikami_zaw_naped, zawieszenie_kalibracja_naped):
        try:
            diagnostyka.dodaj_czujnik(CzujnikZawieszenia(dane_df[odwrotna_tabela_nazw[czujnik_zaw_naped]],
                                                         wartosc_kalibracji=kalibracja, nazwa=czujnik_zaw_naped,
                                                         dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikZawieszenia(None,
                                                         wartosc_kalibracji=kalibracja, nazwa=czujnik_zaw_naped))
            print(f"Brak danych czujnika: {czujnik_zaw_naped}")

    # toczne
    for czujnik_zaw_toczny, kalibracja in zip(kolumny_z_czujnikami_zaw_toczne, zawieszenie_kalibracja_toczne):
        try:
            diagnostyka.dodaj_czujnik(CzujnikZawieszenia(dane_df[odwrotna_tabela_nazw[czujnik_zaw_toczny]],
                                                         wartosc_kalibracji=kalibracja, nazwa=czujnik_zaw_toczny,
                                                         typ_wozka="toczny",
                                                         dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikZawieszenia(None,
                                                         wartosc_kalibracji=kalibracja, nazwa=czujnik_zaw_toczny,
                                                         typ_wozka="toczny"))
            print(f"Brak danych czujnika: {czujnik_zaw_toczny}")

    # cisnienie hamulcow
    for czujnik in kolumny_z_czujnikami_hamulcow:
        try:
            diagnostyka.dodaj_czujnik(CzujnikHamulec(dane_df[odwrotna_tabela_nazw[czujnik]],
                                                     zakres_przeliczone=(0, 30), max_delta=30, nazwa=czujnik,
                                                     dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikHamulec(None,
                                                     zakres_przeliczone=(0, 30), max_delta=30, nazwa=czujnik))
            print(f"Brak danych czujnika: {czujnik}")

    # akcelerometry
    for czujnik in kolumny_z_akcelerometrami:
        try:
            diagnostyka.dodaj_czujnik(CzujnikAkcelerometr(dane_df[odwrotna_tabela_nazw[czujnik]],
                                                          zakres_przeliczone=(0, 32768), max_delta=10000, nazwa=czujnik,
                                                          dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikAkcelerometr(None,
                                                          zakres_przeliczone=(0, 32768), max_delta=10000,
                                                          nazwa=czujnik))
            print(f"Brak danych czujnika: {czujnik}")

    # temperatura silnika i falownika
    for czujnik, (nazwa_silnik, nazwa_falownik) in zip(kolumny_silnik_falownik, nazwy_silnik_falownik):
        try:
            diagnostyka.dodaj_czujnik(CzujnikTemperaturySilnik(dane_df[odwrotna_tabela_nazw[czujnik]],
                                                               zakres_CAN=(0, 2147418112),
                                                               zakres_przeliczone=(-10, 180), nazwa=nazwa_silnik,
                                                               dt_series=seria_dt, vel_series=seria_predkosc))
            diagnostyka.dodaj_czujnik(CzujnikTemperaturyFalownik(dane_df[odwrotna_tabela_nazw[czujnik]],
                                                                 zakres_CAN=(0, 2147418112),
                                                                 zakres_przeliczone=(-10, 100), nazwa=nazwa_falownik,
                                                                 dt_series=seria_dt, vel_series=seria_predkosc))
        except KeyError:
            diagnostyka.dodaj_czujnik(CzujnikTemperaturySilnik(None,
                                                               zakres_przeliczone=(-10, 180), nazwa=nazwa_silnik))
            diagnostyka.dodaj_czujnik(CzujnikTemperaturyFalownik(None,
                                                                 zakres_przeliczone=(-10, 100), nazwa=nazwa_falownik))
            print(f"Brak danych czujnika: {czujnik}")

    tabela_diagnozy = diagnostyka.diagnostyka(zapisz=True)

    return dane_df, tabela_diagnozy

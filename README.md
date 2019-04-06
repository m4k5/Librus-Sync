# LibrusSync

## Instalacja
1. Zainstaluj wymagane biblioteki
```
pip install -r requirements.txt
```
2. Pobierz dane do autoryzacji oauth z [panelu Google APIs](https://console.developers.google.com/apis/credentials) w
postaci pliku json i zmień jego nazwę na `credentials.json`

3. Uruchom (python3 sync.py) i podaj login do Librusa oraz dokonaj autoryzacji oauth dla Google Calendar
4. Ewentualnie zmiany dokonaj w pliku `data.json`, który jest w folderze `.data`

## Uwagi
 - Plik `cache.sqlite` zawiera cache wymagany do szybszego działania aplikacji
 - Jeśli chcesz zresetować aplikację usuń zawartość `.data`
 > **NIE USUWAJ FOLDERU `.data`**
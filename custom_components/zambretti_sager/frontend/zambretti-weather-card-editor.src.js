/**
 * Zambretti & Sager Weather Card Editor
 * Dynamically loaded only when user opens card configuration dialog.
 */

const EDITOR_STRINGS = {
  "en": {"appearance": "Appearance", "language": "Language", "langAuto": "Auto (from Home Assistant)", "cardStyle": "Card Style", "styleModern": "Modern iOS Style", "styleVintage": "Vintage Nautical Barometer", "styleTile": "Compact Tile (Mushroom style)", "vintageUnits": "Dial scale unit", "showSubdial": "Show 3h trend sub-dial", "showSubdialH": "Auxiliary sub-dial with 3-hour pressure change indicator", "showWind": "Show wind", "showWindH": "Wind direction and speed in the footer", "windEntity": "Wind speed sensor", "windEntityH": "Optional — if not set, uses the main sensor attribute", "windUnit": "Wind unit", "showSager": "Show Sager forecast", "showSagerH": "Bottom strip with Sager analytics", "showPrecip": "Show precipitation indicator", "showPrecipH": "Circular gauge on the right", "showForecasts": "Show 6h / 12h / 24h forecasts", "showForecastH": "Bottom row with forecast icons", "autoTheme": "Auto theme by condition", "autoThemeH": "Background color follows current weather condition", "themeAlpha": "Background opacity (Alpha)", "themeAlphaH": "Adjust the transparency of the auto theme background (0–100%)", "customBg": "Custom card background", "customBgH": "CSS gradient or color, e.g. #1a1a2e or linear-gradient(...)", "showTrend": "Show forecast trend timeline", "showTrendH": "Horizontal strip of past Zambretti states with icons and times", "showHistory": "Show 24h history chart", "showHistoryH": "Pressure & precipitation chart for the last 24 hours"},
  "ru": {"appearance": "Внешний вид", "language": "Язык", "langAuto": "Авто (из Home Assistant)", "cardStyle": "Стиль карточки", "styleModern": "Современный стиль (iOS)", "styleVintage": "Винтажный морской барометр", "styleTile": "Компактная плитка (Tile / Mushroom)", "vintageUnits": "Единицы шкалы циферблата", "showSubdial": "Показывать мини-индикатор тренда", "showSubdialH": "Вспомогательный циферблат с дельтой давления за 3 часа", "showWind": "Показывать ветер", "showWindH": "Направление и скорость ветра в нижней полоске", "windEntity": "Датчик скорости ветра", "windEntityH": "Необязательно — если не выбран, используется атрибут основного датчика", "windUnit": "Единицы ветра", "showSager": "Показывать прогноз Sager", "showSagerH": "Нижняя полоска с аналитикой Sager", "showPrecip": "Показывать вероятность осадков", "showPrecipH": "Круговой индикатор справа", "showForecasts": "Показывать прогнозы 6ч / 12ч / 24ч", "showForecastH": "Нижний ряд с иконками", "autoTheme": "Авто-тема по погоде", "autoThemeH": "Цвет фона меняется по текущему условию", "themeAlpha": "Прозрачность фона (Alpha)", "themeAlphaH": "Регулировка прозрачности градиента авто-темы (0–100%)", "customBg": "Свой фон карточки", "customBgH": "CSS-градиент или цвет, напр. #1a1a2e или linear-gradient(...)", "showTrend": "Показывать историю изменений", "showTrendH": "Горизонтальная лента предыдущих прогнозов Zambretti", "showHistory": "Показывать 24ч график", "showHistoryH": "График давления и осадков за последние 24 часа"},
  "fr": {"appearance": "Apparence", "language": "Langue", "langAuto": "Auto (depuis Home Assistant)", "cardStyle": "Style de carte", "styleModern": "Style moderne iOS", "styleVintage": "Baromètre marin vintage", "styleTile": "Tuile compacte (style Mushroom)", "vintageUnits": "Unité du cadran", "showSubdial": "Afficher le sous-cadran de tendance 3h", "showSubdialH": "Cadran auxiliaire avec variation de pression sur 3 heures", "showWind": "Afficher le vent", "showWindH": "Direction et vitesse du vent dans le bandeau inférieur", "windEntity": "Capteur de vitesse du vent", "windEntityH": "Optionnel — si vide, utilise l'attribut du capteur principal", "windUnit": "Unité du vent", "showSager": "Afficher la prévision Sager", "showSagerH": "Bandeau inférieur avec l'analyse Sager", "showPrecip": "Afficher les précipitations", "showPrecipH": "Jauge circulaire à droite", "showForecasts": "Afficher les prévisions 6h / 12h / 24h", "showForecastH": "Rangée inférieure avec les icônes de prévision", "autoTheme": "Thème automatique selon la météo", "autoThemeH": "La couleur de fond suit la condition météo actuelle", "themeAlpha": "Opacité du fond (Alpha)", "themeAlphaH": "Ajuste la transparence du dégradé (0–100%)", "customBg": "Fond personnalisé", "customBgH": "Dégradé CSS ou couleur, ex. #1a1a2e ou linear-gradient(...)", "showTrend": "Afficher la chronologie des prévisions", "showTrendH": "Bandeau horizontal des états Zambretti passés avec icônes", "showHistory": "Afficher le graphique 24h", "showHistoryH": "Graphique de pression et précipitations sur 24 heures"},
  "de": {"appearance": "Darstellung", "language": "Sprache", "langAuto": "Automatisch (von Home Assistant)", "cardStyle": "Kartenstil", "styleModern": "Moderner iOS-Stil", "styleVintage": "Klassisches nautisches Barometer", "styleTile": "Kompakte Kachel (Mushroom-Stil)", "vintageUnits": "Skaleneinheit des Zifferblatts", "showSubdial": "3h-Trend-Teilzifferblatt anzeigen", "showSubdialH": "Zusatzanzeige mit Druckänderung der letzten 3 Stunden", "showWind": "Wind anzeigen", "showWindH": "Windrichtung und -geschwindigkeit in der Fußzeile", "windEntity": "Windgeschwindigkeitssensor", "windEntityH": "Optional — falls leer, Attribut des Hauptsensors", "windUnit": "Windeinheit", "showSager": "Sager-Prognose anzeigen", "showSagerH": "Untere Leiste mit Sager-Analyse", "showPrecip": "Niederschlagsanzeige", "showPrecipH": "Kreisanzeige auf der rechten Seite", "showForecasts": "Prognosen 6h / 12h / 24h anzeigen", "showForecastH": "Untere Zeile mit Vorhersagesymbolen", "autoTheme": "Automatisches Wetterthema", "autoThemeH": "Hintergrundfarbe folgt dem aktuellen Wetter", "themeAlpha": "Hintergrund-Deckkraft (Alpha)", "themeAlphaH": "Transparenz des Verlaufs anpassen (0–100 %)", "customBg": "Benutzerdefinierter Hintergrund", "customBgH": "CSS-Farbverlauf oder Farbe, z. B. #1a1a2e oder linear-gradient(...)", "showTrend": "Vorhersage-Trendleiste anzeigen", "showTrendH": "Horizontale Leiste früherer Zambretti-Zustände mit Symbolen", "showHistory": "24h-Verlaufsdiagramm anzeigen", "showHistoryH": "Druck- und Niederschlagsdiagramm der letzten 24 Stunden"},
  "es": {"appearance": "Apariencia", "language": "Idioma", "langAuto": "Automático (desde Home Assistant)", "cardStyle": "Estilo de tarjeta", "styleModern": "Estilo moderno iOS", "styleVintage": "Barómetro náutico vintage", "styleTile": "Tarjeta compacta (estilo Mushroom)", "vintageUnits": "Unidad de la escala", "showSubdial": "Mostrar subesfera de tendencia de 3h", "showSubdialH": "Subesfera auxiliar con variación de presión en 3 horas", "showWind": "Mostrar viento", "showWindH": "Dirección y velocidad del viento en el pie", "windEntity": "Sensor de velocidad del viento", "windEntityH": "Opcional — si no se define, usa el atributo del sensor principal", "windUnit": "Unidad de viento", "showSager": "Mostrar pronóstico Sager", "showSagerH": "Banda inferior con analítica Sager", "showPrecip": "Mostrar probabilidad de precipitación", "showPrecipH": "Indicador circular a la derecha", "showForecasts": "Mostrar pronósticos 6h / 12h / 24h", "showForecastH": "Fila inferior con iconos de previsión", "autoTheme": "Tema automático según el tiempo", "autoThemeH": "El color de fondo sigue las condiciones actuales", "themeAlpha": "Opacidad del fondo (Alpha)", "themeAlphaH": "Ajustar la transparencia del fondo automático (0–100%)", "customBg": "Fondo personalizado", "customBgH": "Degradado CSS o color, p. ej. #1a1a2e o linear-gradient(...)", "showTrend": "Mostrar cronología de tendencias", "showTrendH": "Franja horizontal con estados previos de Zambretti", "showHistory": "Mostrar gráfico de 24h", "showHistoryH": "Gráfico de presión y precipitación de las últimas 24 horas"},
  "it": {"appearance": "Aspetto", "language": "Lingua", "langAuto": "Automatico (da Home Assistant)", "cardStyle": "Stile scheda", "styleModern": "Stile moderno iOS", "styleVintage": "Barometro nautico vintage", "styleTile": "Riquadro compatto (stile Mushroom)", "vintageUnits": "Unità quadrante", "showSubdial": "Mostra sottoquadrante tendenza 3h", "showSubdialH": "Quadrante ausiliario con delta di pressione su 3 ore", "showWind": "Mostra vento", "showWindH": "Direzione e velocità del vento nel piè di pagina", "windEntity": "Sensore velocità vento", "windEntityH": "Opzionale — se vuoto, usa l'attributo del sensore principale", "windUnit": "Unità vento", "showSager": "Mostra previsione Sager", "showSagerH": "Striscia inferiore con analisi Sager", "showPrecip": "Mostra probabilità precipitazioni", "showPrecipH": "Indicatore circolare a destra", "showForecasts": "Mostra previsioni 6h / 12h / 24h", "showForecastH": "Riga inferiore con icone di previsione", "autoTheme": "Tema automatico per condizione", "autoThemeH": "Il colore di sfondo segue il meteo attuale", "themeAlpha": "Opacità dello sfondo (Alpha)", "themeAlphaH": "Regola la trasparenza del gradiente (0–100%)", "customBg": "Sfondo personalizzato", "customBgH": "Gradiente CSS o colore, es. #1a1a2e o linear-gradient(...)", "showTrend": "Mostra cronologia previsioni", "showTrendH": "Striscia orizzontale degli stati Zambretti precedenti", "showHistory": "Mostra grafico 24h", "showHistoryH": "Grafico di pressione e precipitazioni delle ultime 24 ore"},
  "pl": {"appearance": "Wygląd", "language": "Język", "langAuto": "Automatycznie (z Home Assistant)", "cardStyle": "Styl karty", "styleModern": "Nowoczesny styl iOS", "styleVintage": "Klasyczny barometr morski", "styleTile": "Kompaktowa płytka (styl Mushroom)", "vintageUnits": "Jednostka tarczy", "showSubdial": "Pokaż minitarczę trendu 3h", "showSubdialH": "Pomocnicza tarcza ze zmianą ciśnienia w ciągu 3 godzin", "showWind": "Pokaż wiatr", "showWindH": "Kierunek i prędkość wiatru w stopce", "windEntity": "Czujnik prędkości wiatru", "windEntityH": "Opcjonalnie — domyślnie atrybut głównego czujnika", "windUnit": "Jednostka wiatru", "showSager": "Pokaż prognozę Sager", "showSagerH": "Dolny pasek z analityką Sager", "showPrecip": "Pokaż prawdopodobieństwo opadów", "showPrecipH": "Okrągły wskaźnik po prawej stronie", "showForecasts": "Pokaż prognozy 6h / 12h / 24h", "showForecastH": "Dolny wiersz z ikonami prognozy", "autoTheme": "Automatyczny motyw wg pogody", "autoThemeH": "Kolor tła dostosowuje się do aktualnej pogody", "themeAlpha": "Przezroczystość tła (Alpha)", "themeAlphaH": "Regulacja przezroczystości tła (0–100%)", "customBg": "Własne tło karty", "customBgH": "Gradient CSS lub kolor, np. #1a1a2e lub linear-gradient(...)", "showTrend": "Pokaż oś czasu trendu prognozy", "showTrendH": "Poziomy pasek poprzednich stanów Zambretti", "showHistory": "Pokaż wykres 24h", "showHistoryH": "Wykres ciśnienia i opadów z ostatnich 24 godzin"},
  "nl": {"appearance": "Uiterlijk", "language": "Taal", "langAuto": "Automatisch (van Home Assistant)", "cardStyle": "Kaartstijl", "styleModern": "Moderne iOS-stijl", "styleVintage": "Klassieke maritieme barometer", "styleTile": "Compacte tegel (Mushroom-stijl)", "vintageUnits": "Schaaleenheid wijzerplaat", "showSubdial": "Toon 3-uurs trend wijzerplaat", "showSubdialH": "Hulpwijzerplaat met drukverandering over 3 uur", "showWind": "Toon wind", "showWindH": "Windrichting en snelheid in de voettekst", "windEntity": "Windsnelheidssensor", "windEntityH": "Optioneel — gebruikt anders het attribuut van de hoofdsensor", "windUnit": "Windeenheid", "showSager": "Toon Sager-voorspelling", "showSagerH": "Onderste balk met Sager-analyse", "showPrecip": "Toon neerslagindicator", "showPrecipH": "Cirkelvormige meter aan de rechterkant", "showForecasts": "Toon voorspellingen 6u / 12u / 24u", "showForecastH": "Onderste rij met weerspictogrammen", "autoTheme": "Automatisch thema op basis van weer", "autoThemeH": "Achtergrondkleur volgt de actuele weersomstandigheden", "themeAlpha": "Achtergronddekking (Alpha)", "themeAlphaH": "Pas de transparantie van het thema aan (0–100%)", "customBg": "Aangepaste achtergrond", "customBgH": "CSS-verloop of kleur, bijv. #1a1a2e of linear-gradient(...)", "showTrend": "Toon tijdlijn voorspellingstrend", "showTrendH": "Horizontale balk met eerdere Zambretti-toestanden", "showHistory": "Toon 24-uurs grafiek", "showHistoryH": "Luchtdruk- en neerslaggrafiek voor de afgelopen 24 uur"},
  "pt": {"appearance": "Aparência", "language": "Idioma", "langAuto": "Automático (do Home Assistant)", "cardStyle": "Estilo do cartão", "styleModern": "Estilo moderno iOS", "styleVintage": "Barómetro náutico vintage", "styleTile": "Mosaico compacto (estilo Mushroom)", "vintageUnits": "Unidade da escala", "showSubdial": "Mostrar mostrador de tendência 3h", "showSubdialH": "Mostrador auxiliar com variação de pressão em 3 horas", "showWind": "Mostrar vento", "showWindH": "Direção e velocidade do vento no rodapé", "windEntity": "Sensor de velocidade do vento", "windEntityH": "Opcional — se não definido, usa o atributo do sensor principal", "windUnit": "Unidade de vento", "showSager": "Mostrar previsão Sager", "showSagerH": "Faixa inferior com análise Sager", "showPrecip": "Mostrar indicador de precipitação", "showPrecipH": "Indicador circular à direita", "showForecasts": "Mostrar previsões 6h / 12h / 24h", "showForecastH": "Linha inferior com ícones de previsão", "autoTheme": "Tema automático conforme o tempo", "autoThemeH": "A cor de fundo segue a condição meteorológica atual", "themeAlpha": "Opacidade do fundo (Alpha)", "themeAlphaH": "Ajusta a transparência do gradiente (0–100%)", "customBg": "Fundo personalizado", "customBgH": "Gradiente CSS ou cor, ex: #1a1a2e ou linear-gradient(...)", "showTrend": "Mostrar linha do tempo da tendência", "showTrendH": "Faixa horizontal de estados anteriores do Zambretti", "showHistory": "Mostrar gráfico de 24h", "showHistoryH": "Gráfico de pressão e precipitação das últimas 24 horas"},
  "uk": {"appearance": "Зовнішній вигляд", "language": "Мова", "langAuto": "Авто (з Home Assistant)", "cardStyle": "Стиль картки", "styleModern": "Сучасний стиль (iOS)", "styleVintage": "Вінтажний морський барометр", "styleTile": "Компактна плитка (Tile / Mushroom)", "vintageUnits": "Одиниці шкали циферблата", "showSubdial": "Показувати міні-індикатор тренду", "showSubdialH": "Допоміжний циферблат з дельтою тиску за 3 години", "showWind": "Показувати вітер", "showWindH": "Напрямок та швидкість вітру в нижній смужці", "windEntity": "Датчик швидкості вітру", "windEntityH": "Необов'язково — якщо не вибрано, використовується атрибут основного датчика", "windUnit": "Одиниці вітру", "showSager": "Показувати прогноз Sager", "showSagerH": "Нижня смужка з аналітикою Sager", "showPrecip": "Показувати ймовірність опадів", "showPrecipH": "Круговий індикатор праворуч", "showForecasts": "Показувати прогнози 6г / 12г / 24г", "showForecastH": "Нижній ряд з іконками", "autoTheme": "Авто-тема за погодою", "autoThemeH": "Колір фону змінюється відповідно до поточної погоди", "themeAlpha": "Прозорість фону (Alpha)", "themeAlphaH": "Регулювання прозорості градієнта авто-теми (0–100%)", "customBg": "Власний фон картки", "customBgH": "CSS-градієнт або колір, напр. #1a1a2e або linear-gradient(...)", "showTrend": "Показувати історію змін", "showTrendH": "Горизонтальна стрічка попередніх прогнозів Zambretti", "showHistory": "Показувати 24г графік", "showHistoryH": "График тиску та опадів за останні 24 години"},
  "zh-Hans": {"appearance": "外观", "language": "语言", "langAuto": "自动（跟随 Home Assistant）", "cardStyle": "卡片样式", "styleModern": "现代 iOS 风格", "styleVintage": "经典航海气压计", "styleTile": "紧凑磁贴（Mushroom 风格）", "vintageUnits": "表盘刻度单位", "showSubdial": "显示 3 小时趋势子表盘", "showSubdialH": "带有 3 小时气压变化指示的辅助表盘", "showWind": "显示风速", "showWindH": "在底部栏显示风向和风速", "windEntity": "风速传感器", "windEntityH": "可选 — 未设置则使用主传感器属性", "windUnit": "风速单位", "showSager": "显示 Sager 预报", "showSagerH": "包含 Sager 分析的底部条", "showPrecip": "显示降水概率", "showPrecipH": "右侧圆形仪表", "showForecasts": "显示 6/12/24 小时预报", "showForecastH": "带有预报图标的底部行", "autoTheme": "天气自动主题", "autoThemeH": "背景颜色跟随当前天气变化", "themeAlpha": "背景不透明度 (Alpha)", "themeAlphaH": "调节自动主题背景透明度 (0–100%)", "customBg": "自定义卡片背景", "customBgH": "CSS 渐变或颜色，例如 #1a1a2e 或 linear-gradient(...)", "showTrend": "显示预报趋势时间线", "showTrendH": "包含图标和时间的 Zambretti 历史状态横条", "showHistory": "显示 24 小时历史图表", "showHistoryH": "过去 24 小时的气压与降水图表"},
  "zh-Hant": {"appearance": "外觀", "language": "語言", "langAuto": "自動（跟隨 Home Assistant）", "cardStyle": "卡片樣式", "styleModern": "現代 iOS 風格", "styleVintage": "經典航海氣壓計", "styleTile": "緊湊磁貼（Mushroom 風格）", "vintageUnits": "錶盤刻度單位", "showSubdial": "顯示 3 小時趨勢子錶盤", "showSubdialH": "帶有 3 小時氣壓變化指示的輔助錶盤", "showWind": "顯示風速", "showWindH": "在底部列顯示風向和風速", "windEntity": "風速感測器", "windEntityH": "選填 — 未設定則使用主感測器屬性", "windUnit": "風速單位", "showSager": "顯示 Sager 預報", "showSagerH": "包含 Sager 分析的底部列", "showPrecip": "顯示降水機率", "showPrecipH": "右側圓形儀表", "showForecasts": "顯示 6/12/24 小時預報", "showForecastH": "帶有預報圖示的底部列", "autoTheme": "天氣自動主題", "autoThemeH": "背景顏色跟隨當前天氣變化", "themeAlpha": "背景不透明度 (Alpha)", "themeAlphaH": "調整自動主題背景透明度 (0–100%)", "customBg": "自訂卡片背景", "customBgH": "CSS 漸變或顏色，例如 #1a1a2e 或 linear-gradient(...)", "showTrend": "顯示預報趨勢時間線", "showTrendH": "包含圖示與時間的 Zambretti 歷史狀態橫條", "showHistory": "顯示 24 小時歷史圖表", "showHistoryH": "過去 24 小時的氣壓與降水圖表"},
  "ja": {"appearance": "外観", "language": "言語", "langAuto": "自動（Home Assistant に準拠）", "cardStyle": "カードスタイル", "styleModern": "モダン iOS スタイル", "styleVintage": "ビンテージ航海気圧計", "styleTile": "コンパクトタイル（Mushroom風）", "vintageUnits": "ダイヤル目盛単位", "showSubdial": "3時間トレンドサブダイヤルを表示", "showSubdialH": "3時間の気圧変化を表示する補助サブダイヤル", "showWind": "風を表示", "showWindH": "フッターに風向と風速を表示", "windEntity": "風速センサー", "windEntityH": "オプション — 未設定時はメインセンサーの属性を使用", "windUnit": "風速単位", "showSager": "Sager 予報を表示", "showSagerH": "Sager 分析を含む下部バー", "showPrecip": "降水確率を表示", "showPrecipH": "右側の円形ゲージ", "showForecasts": "6/12/24時間予報を表示", "showForecastH": "予報アイコン付きの下部行", "autoTheme": "天候に応じた自動テーマ", "autoThemeH": "背景色が現在の天候に連動", "themeAlpha": "背景の不透明度 (Alpha)", "themeAlphaH": "自動テーマの背景透明度を調整 (0–100%)", "customBg": "カスタムカード背景", "customBgH": "CSSグラデーションまたは色、例: #1a1a2e や linear-gradient(...)", "showTrend": "予報トレンドタイムラインを表示", "showTrendH": "過去の Zambretti 状態と時刻の横帯", "showHistory": "24時間履歴グラフを表示", "showHistoryH": "過去24時間の気圧・降水グラフ"},
  "ko": {"appearance": "외형", "language": "언어", "langAuto": "자동 (Home Assistant 기준)", "cardStyle": "카드 스타일", "styleModern": "모던 iOS 스타일", "styleVintage": "빈티지 해양 기압계", "styleTile": "컴팩트 타일 (Mushroom 스타일)", "vintageUnits": "다이얼 눈금 단위", "showSubdial": "3시간 트렌드 보조 다이얼 표시", "showSubdialH": "3시간 기압 변화 표시 보조 다이얼", "showWind": "바람 표시", "showWindH": "하단에 풍향 및 풍속 표시", "windEntity": "풍속 센서", "windEntityH": "선택 사항 — 설정하지 않으면 기본 센서 속성 사용", "windUnit": "풍속 단위", "showSager": "Sager 예보 표시", "showSagerH": "Sager 분석 하단 바", "showPrecip": "강수 확률 표시", "showPrecipH": "우측 원형 게이지", "showForecasts": "6/12/24시간 예보 표시", "showForecastH": "예보 아이콘 하단 행", "autoTheme": "날씨에 따른 자동 테마", "autoThemeH": "배경색이 현재 날씨에 맞춰 변경됨", "themeAlpha": "배경 불투명도 (Alpha)", "themeAlphaH": "자동 테마 배경 투명도 조절 (0–100%)", "customBg": "사용자 지정 배경", "customBgH": "CSS 그라디언트 또는 색상, 예: #1a1a2e 또는 linear-gradient(...)", "showTrend": "예보 트렌드 타임라인 표시", "showTrendH": "이전 Zambretti 상태 및 시간 가로 바", "showHistory": "24시간 기록 그래프 표시", "showHistoryH": "최근 24시간 기압 및 강수 그래프"},
  "cs": {"appearance": "Vzhled", "language": "Jazyk", "langAuto": "Automaticky (z Home Assistant)", "cardStyle": "Styl karty", "styleModern": "Moderní styl iOS", "styleVintage": "Klasický námořní barometr", "styleTile": "Kompaktní dlaždice (styl Mushroom)", "vintageUnits": "Jednotka stupnice ciferníku", "showSubdial": "Zobrazit dílčí ciferník 3h trendu", "showSubdialH": "Pomocný ciferník s ukazatelem změny tlaku za 3 hodiny", "showWind": "Zobrazit vítr", "showWindH": "Směr a rychlost větru v zápatí", "windEntity": "Senzor rychlosti větru", "windEntityH": "Volitelné — pokud není nastaveno, použije se atribut hlavního senzoru", "windUnit": "Jednotka větru", "showSager": "Zobrazit předpověď Sager", "showSagerH": "Dolní pruh s analýzou Sager", "showPrecip": "Zobrazit ukazatel srážek", "showPrecipH": "Kruhový ukazatel vpravo", "showForecasts": "Zobrazit předpovědi 6h / 12h / 24h", "showForecastH": "Dolní řádek s ikonami předpovědi", "autoTheme": "Automatický motiv podle počasí", "autoThemeH": "Barva pozadí odpovídá aktuálnímu počasí", "themeAlpha": "Průhlednost pozadí (Alfa)", "themeAlphaH": "Nastavení průhlednosti pozadí automatického motivu (0–100 %)", "customBg": "Vlastní pozadí karty", "customBgH": "CSS přechod nebo barva, např. #1a1a2e nebo linear-gradient(...)", "showTrend": "Zobrazit časovou osu trendu předpovědi", "showTrendH": "Vodorovný pás minulých stavů Zambretti s ikonami a časy", "showHistory": "Zobrazit 24h graf historie", "showHistoryH": "Graf tlaku a srážek za posledních 24 hodin"},
  "sv": {"appearance": "Utseende", "language": "Språk", "langAuto": "Automatiskt (från Home Assistant)", "cardStyle": "Kortstil", "styleModern": "Modern iOS-stil", "styleVintage": "Klassisk maritim barometer", "styleTile": "Kompakt bricka (Mushroom-stil)", "vintageUnits": "Skalenhet för urtavla", "showSubdial": "Visa 3-timmars trendsuburtavla", "showSubdialH": "Hjälpurtavla med indikator för 3-timmars tryckförändring", "showWind": "Visa vind", "showWindH": "Vindriktning och hastighet i sidfoten", "windEntity": "Vindhastighetssensor", "windEntityH": "Valfritt — om ej inställt används huvudsensorns attribut", "windUnit": "Vindenhet", "showSager": "Visa Sager-prognos", "showSagerH": "Bottenlist med Sager-analys", "showPrecip": "Visa nederbördsindikator", "showPrecipH": "Cirkulär mätare till höger", "showForecasts": "Visa 6h / 12h / 24h prognoser", "showForecastH": "Bottenrad med prognosikoner", "autoTheme": "Automatiskt tema efter väder", "autoThemeH": "Bakgrundsfärgen följer aktuellt väderläge", "themeAlpha": "Bakgrundens opacitet (Alfa)", "themeAlphaH": "Justera opaciteten för det automatiska temat (0–100 %)", "customBg": "Anpassad kortbakgrund", "customBgH": "CSS-gradient eller färg, t.ex. #1a1a2e eller linear-gradient(...)", "showTrend": "Visa tidslinje för prognostrend", "showTrendH": "Horisontell remsa med tidigare Zambretti-tillstånd och ikoner", "showHistory": "Visa 24h historikdiagram", "showHistoryH": "Tryck- och nederbördsdiagram för de senaste 24 timmarna"},
  "da": {"appearance": "Udseende", "language": "Sprog", "langAuto": "Automatisk (fra Home Assistant)", "cardStyle": "Kortstil", "styleModern": "Moderne iOS-stil", "styleVintage": "Klassisk maritimt barometer", "styleTile": "Kompakt flise (Mushroom-stil)", "vintageUnits": "Skalaenhed for urskive", "showSubdial": "Vis 3-timers trendurskive", "showSubdialH": "Ekstra urskive med 3-timers trykændringsindikator", "showWind": "Vis vind", "showWindH": "Vindretning og hastighed i bunden", "windEntity": "Vindhastighedssensor", "windEntityH": "Valgfrit — hvis ikke indstillet, bruges hovedsensorens attribut", "windUnit": "Vindenhed", "showSager": "Vis Sager-prognose", "showSagerH": "Bundbjælke med Sager-analyse", "showPrecip": "Vis nedbørsindikator", "showPrecipH": "Cirkulær måler til højre", "showForecasts": "Vis 6t / 12t / 24t prognoser", "showForecastH": "Nederste række med prognoseikoner", "autoTheme": "Automatisk tema efter vejr", "autoThemeH": "Baggrundsfarven følger aktuelle vejrforhold", "themeAlpha": "Baggrundens uigennemsigtighed (Alfa)", "themeAlphaH": "Juster gennemsigtigheden af baggrunden (0–100 %)", "customBg": "Brugerdefineret kortbaggrund", "customBgH": "CSS-gradient eller farve, f.eks. #1a1a2e eller linear-gradient(...)", "showTrend": "Vis tidslinje for prognosetrend", "showTrendH": "Vandret bjælke med tidligere Zambretti-tilstande og ikoner", "showHistory": "Vis 24-timers historikgraf", "showHistoryH": "Tryk- og nedbørsdiagram for de sidste 24 timer"},
  "nb": {"appearance": "Utseende", "language": "Språk", "langAuto": "Automatisk (fra Home Assistant)", "cardStyle": "Kortstil", "styleModern": "Moderne iOS-stil", "styleVintage": "Klassisk maritimt barometer", "styleTile": "Kompakt flis (Mushroom-stil)", "vintageUnits": "Skalaenhet for urskive", "showSubdial": "Vis 3-timers trendurskive", "showSubdialH": "Ekstra urskive med 3-timers trykkendringsindikator", "showWind": "Vis vind", "showWindH": "Vindretning og hastighet i bunnteksten", "windEntity": "Vindhastighetssensor", "windEntityH": "Valgfritt — hvis ikke angitt, brukes hovedsensorens attributt", "windUnit": "Vindenhet", "showSager": "Vis Sager-prognose", "showSagerH": "Bunnlinje med Sager-analyse", "showPrecip": "Vis nedbørsindikator", "showPrecipH": "Rund måler til høyre", "showForecasts": "Vis 6t / 12t / 24t prognoser", "showForecastH": "Nederste rad med værikoner", "autoTheme": "Automatisk tema etter vær", "autoThemeH": "Bakgrunnsfargen følger gjeldende værforhold", "themeAlpha": "Bakgrunnsugjennomsiktighet (Alfa)", "themeAlphaH": "Juster gjennomsiktigheten for bakgrunnen (0–100 %)", "customBg": "Egendefinert kortbakgrunn", "customBgH": "CSS-gradient eller farge, f.eks. #1a1a2e eller linear-gradient(...)", "showTrend": "Vis tidslinje for prognosetrend", "showTrendH": "Horisontal stripe med tidligere Zambretti-tilstander og ikoner", "showHistory": "Vis 24t historikkgraf", "showHistoryH": "Trykk- og nedbørsdiagram for de siste 24 timene"},
  "hu": {"appearance": "Megjelenés", "language": "Nyelv", "langAuto": "Automatikus (Home Assistant alapján)", "cardStyle": "Kártyastílus", "styleModern": "Modern iOS stílus", "styleVintage": "Klasszikus tengerészeti barométer", "styleTile": "Kompakt csempe (Mushroom stílus)", "vintageUnits": "Számlap mértékegysége", "showSubdial": "3 órás trend segédszámlap mutatása", "showSubdialH": "Kiegészítő számlap 3 órás légnyomásváltozás-jelzővel", "showWind": "Szél mutatása", "showWindH": "Szélirány és szélsebesség a láblécben", "windEntity": "Szélsebesség érzékelő", "windEntityH": "Opcionális — ha nincs megadva, a fő érzékelő attribútumát használja", "windUnit": "Szél mértékegysége", "showSager": "Sager előrejelzés mutatása", "showSagerH": "Alsó sáv Sager elemzéssel", "showPrecip": "Csapadékjelző mutatása", "showPrecipH": "Kör alakú műszer a jobb oldalon", "showForecasts": "6ó / 12ó / 24ó előrejelzések mutatása", "showForecastH": "Alsó sor előrejelzési ikonokkal", "autoTheme": "Automatikus téma időjárás szerint", "autoThemeH": "A háttérszín követi az aktuális időjárást", "themeAlpha": "Háttér átlátszatlansága (Alfa)", "themeAlphaH": "Az automatikus téma hátterének átlátszósága (0–100%)", "customBg": "Egyéni kártyaháttér", "customBgH": "CSS színátmenet vagy szín, pl. #1a1a2e vagy linear-gradient(...)", "showTrend": "Előrejelzési trend idővonal mutatása", "showTrendH": "Korábbi Zambretti állapotok vízszintes sávja ikonokkal és időpontokkal", "showHistory": "24 órás előzménygrafikon mutatása", "showHistoryH": "Légnyomás és csapadék grafikon az elmúlt 24 órára"},
  "tr": {"appearance": "Görünüm", "language": "Dil", "langAuto": "Otomatik (Home Assistant'tan)", "cardStyle": "Kart Stili", "styleModern": "Modern iOS Stili", "styleVintage": "Klasik Deniz Barometresi", "styleTile": "Kompakt Karo (Mushroom stili)", "vintageUnits": "Kadran ölçek birimi", "showSubdial": "3 saatlik trend alt kadranını göster", "showSubdialH": "3 saatlik basınç değişimi göstergeli yardımcı kadran", "showWind": "Rüzgarı göster", "showWindH": "Alt bilgide rüzgar yönü ve hızı", "windEntity": "Rüzgar hızı sensörü", "windEntityH": "İsteğe bağlı — ayarlanmazsa ana sensör özniteliğini kullanır", "windUnit": "Rüzgar birimi", "showSager": "Sager tahminini göster", "showSagerH": "Sager analitiği içeren alt şerit", "showPrecip": "Yağış göstergesini göster", "showPrecipH": "Sağdaki dairesel gösterge", "showForecasts": "6s / 12s / 24s tahminlerini göster", "showForecastH": "Tahmin simgeleri içeren alt satır", "autoTheme": "Hava durumuna göre otomatik tema", "autoThemeH": "Arka plan rengi geçerli hava durumunu takip eder", "themeAlpha": "Arka plan opaklığı (Alfa)", "themeAlphaH": "Otomatik tema arka planının şeffaflığını ayarlayın (%0–100)", "customBg": "Özel kart arka planı", "customBgH": "CSS gradyanı veya renk, örn. #1a1a2e veya linear-gradient(...)", "showTrend": "Tahmin trendi zaman çizelgesini göster", "showTrendH": "Simgeler ve zamanlarla geçmiş Zambretti durumlarının yatay şeridi", "showHistory": "24 saatlik geçmiş grafiğini göster", "showHistoryH": "Son 24 saatin basınç ve yağış grafiği"}
};

const LANG_OPTIONS = [
  ["auto", "langAuto"],
  ["en", "English"],
  ["de", "Deutsch"],
  ["es", "Español"],
  ["fr", "Français"],
  ["it", "Italiano"],
  ["nl", "Nederlands"],
  ["pl", "Polski"],
  ["pt", "Português"],
  ["ru", "Русский"],
  ["uk", "Українська"],
  ["zh-Hans", "简体中文"],
  ["zh-Hant", "繁體中文"],
  ["ja", "日本語"],
  ["ko", "한국어"],
  ["cs", "Čeština"],
  ["sv", "Svenska"],
  ["da", "Dansk"],
  ["nb", "Norsk"],
  ["hu", "Magyar"],
  ["tr", "Türkçe"]
];

function resolveLang(lang) {
  if (!lang) return 'en';
  if (lang === 'auto') return 'auto';
  if (lang.startsWith('zh')) return lang.includes('Hant') ? 'zh-Hant' : 'zh-Hans';
  if (lang.startsWith('pt')) return 'pt';
  if (lang.startsWith('nb') || lang.startsWith('no')) return 'nb';
  const base = lang.split('-')[0];
  if (EDITOR_STRINGS[lang]) return lang;
  if (EDITOR_STRINGS[base]) return base;
  return 'en';
}

function getEditorStrings(configLang, hassLang) {
  const code = configLang === 'auto' ? resolveLang(hassLang || 'en') : resolveLang(configLang);
  return EDITOR_STRINGS[code] || EDITOR_STRINGS.en;
}

class ZambrettiWeatherCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode:"open"});
    this._config = {};
  }

  setConfig(config) { this._config = {...config}; this._render(); }
  set hass(h) {
    this._hass = h;
    this._syncPickers();
    if (this.shadowRoot?.querySelector("#wind-entity-picker")
        && !this.shadowRoot.querySelector("ha-entity-picker")) {
      this._setupWindEntityPicker();
    }
  }

  _applyBgToCard(bg) {
    window.dispatchEvent(new CustomEvent("zambretti-bg-preview", {detail:{bg}}));
  }

  _fire(config) {
    this.dispatchEvent(new CustomEvent("config-changed",
      {detail:{config}, bubbles:true, composed:true}));
  }

  _render() {
    const c = this._config;
    const lang = c.language || "auto";
    const hLang = this._hass?.language || "en";
    const t = getEditorStrings(lang, hLang);

    const autoThemeOn  = c.auto_theme !== false;
    const themeAlpha   = c.theme_alpha ?? 100;
    const showWindOn   = c.show_wind !== false;
    const customBg     = c.custom_bg || "linear-gradient(135deg,#1565C0 0%,#1976D2 100%)";
    const isSolidColor = /^#[0-9a-fA-F]{3,8}$/.test(customBg.trim());
    const colorInputVal= isSolidColor ? customBg.trim() : "#1565C0";
    const windUnit     = c.wind_unit || "m/s";

    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;padding:4px 0 8px}
        .section-title{font-size:0.70rem;font-weight:700;letter-spacing:.10em;
          text-transform:uppercase;color:var(--secondary-text-color);
          margin:16px 0 6px;padding-left:2px}
        .field-row{margin-bottom:10px}
        .field-row label{display:block;font-size:0.82rem;
          color:var(--secondary-text-color);margin-bottom:4px}
        .field-hint{font-size:0.72rem;color:var(--secondary-text-color);margin-top:2px}
        select,input[type=text]{
          width:100%;padding:9px 12px;border-radius:8px;box-sizing:border-box;
          border:1px solid var(--divider-color,rgba(255,255,255,0.15));
          background:var(--card-background-color,#1e1e1e);
          color:var(--primary-text-color,#fff);font-size:0.92rem;cursor:pointer}
        .row{display:flex;align-items:center;justify-content:space-between;
          padding:10px 2px;border-bottom:1px solid var(--divider-color,rgba(0,0,0,.10))}
        .row:last-child{border-bottom:none}
        .row-label{font-size:0.95rem;color:var(--primary-text-color)}
        .row-hint{font-size:0.75rem;color:var(--secondary-text-color);margin-top:2px}
        .custom-bg-row{padding:10px 2px 12px;
          border-bottom:1px solid var(--divider-color,rgba(0,0,0,.10))}
        .bg-inputs{display:flex;gap:8px;align-items:center;margin-top:6px}
        .bg-color-swatch{width:36px;height:36px;border-radius:8px;
          border:2px solid rgba(255,255,255,0.2);cursor:pointer;
          flex-shrink:0;overflow:hidden;position:relative}
        .bg-color-swatch input[type=color]{position:absolute;inset:0;
          width:100%;height:100%;border:none;padding:0;cursor:pointer;opacity:0}
        .bg-color-preview{position:absolute;inset:0;border-radius:6px;pointer-events:none}
        .bg-text-input{flex:1;padding:8px 10px;border-radius:8px;
          border:1px solid var(--divider-color,rgba(255,255,255,0.15));
          background:var(--card-background-color,#1e1e1e);
          color:var(--primary-text-color,#fff);font-size:0.85rem;font-family:monospace}
      </style>

      <div class="section-title">${t.appearance}</div>

      <div class="field-row">
        <label>${t.cardStyle || "Card Style"}</label>
        <select id="sel-card-style">
          <option value="modern" ${c.card_style !== "vintage" && c.card_style !== "tile" ? "selected" : ""}>${t.styleModern || "Modern iOS Style"}</option>
          <option value="vintage" ${c.card_style === "vintage" ? "selected" : ""}>${t.styleVintage || "Vintage Nautical Barometer"}</option>
          <option value="tile" ${c.card_style === "tile" ? "selected" : ""}>${t.styleTile || "Compact Tile (Mushroom style)"}</option>
        </select>
      </div>

      ${c.card_style === "vintage" ? `
      ${this._toggle("sw-subdial", t.showSubdial || "Show 3h trend sub-dial", t.showSubdialH || "Auxiliary sub-dial with 3-hour pressure change indicator", c.show_subdial !== false)}
      ` : ""}

      <div class="field-row">
        <label>${t.language}</label>
        <select id="sel-lang">
          ${LANG_OPTIONS.map(([value, label]) => {
            const text = value === "auto" ? t.langAuto : label;
            const selected = lang === value ? "selected" : "";
            return `<option value="${value}" ${selected}>${text}</option>`;
          }).join("")}
        </select>
      </div>

      ${this._toggle("sw-wind", t.showWind, t.showWindH, showWindOn)}

      ${showWindOn ? `
      <div class="field-row">
        <label>${t.windEntity}</label>
        <div id="wind-entity-picker"></div>
        <div class="field-hint">${t.windEntityH}</div>
      </div>

      <div class="field-row">
        <label>${t.windUnit}</label>
        <select id="sel-wind-unit">
          <option value="m/s"  ${windUnit==="m/s" ?"selected":""}>m/s</option>
          <option value="km/h" ${windUnit==="km/h"?"selected":""}>km/h</option>
          <option value="mph"  ${windUnit==="mph" ?"selected":""}>mph</option>
          <option value="kn"   ${windUnit==="kn"  ?"selected":""}>kn</option>
        </select>
      </div>` : ""}

      ${this._toggle("sw-auto-theme", t.autoTheme, t.autoThemeH, autoThemeOn)}
      ${autoThemeOn ? `
      <div class="custom-bg-row">
        <div class="row-label">${t.themeAlpha || "Background opacity (Alpha)"}</div>
        <div class="row-hint">${t.themeAlphaH || "Adjust the transparency of the auto theme background (0–100%)"}</div>
        <div style="display:flex; align-items:center; gap:10px; margin-top:8px;">
          <input type="range" id="theme-alpha-slider" min="0" max="100" value="${themeAlpha}" style="flex:1; cursor:pointer;">
          <span id="theme-alpha-lbl" style="font-size:0.85rem; font-family:monospace; width:40px; text-align:right;">${themeAlpha}%</span>
        </div>
      </div>` : ""}
      ${!autoThemeOn ? `
      <div class="custom-bg-row">
        <div class="row-label">${t.customBg}</div>
        <div class="row-hint">${t.customBgH}</div>
        <div class="bg-inputs">
          <div class="bg-color-swatch">
            <div class="bg-color-preview" id="bg-preview" style="background:${customBg}"></div>
            <input type="color" id="bg-color-picker" value="${colorInputVal}">
          </div>
          <input type="text" class="bg-text-input" id="bg-text"
            value="${customBg.replace(/"/g,'&quot;')}"
            placeholder="linear-gradient(...) or #hex" spellcheck="false">
        </div>
      </div>` : ""}
      ${this._toggle("sw-sager",     t.showSager,     t.showSagerH,    c.show_sager     !== false)}
      ${this._toggle("sw-precip",    t.showPrecip,    t.showPrecipH,   c.show_precip    !== false)}
      ${this._toggle("sw-forecasts", t.showForecasts, t.showForecastH, c.show_forecasts !== false)}
      ${this._toggle("sw-trend",     t.showTrend    || "Show forecast trend timeline", t.showTrendH    || "Horizontal strip of past Zambretti states with icons and times", !!c.show_trend)}
      ${this._toggle("sw-history",   t.showHistory  || "Show 24h history chart",      t.showHistoryH  || "Pressure & precipitation chart for the last 24 hours",            !!c.show_history)}
    `;

    // Event listeners
    const cardStyleSel = this.shadowRoot.querySelector("#sel-card-style");
    if (cardStyleSel) {
      cardStyleSel.addEventListener("change", e => {
        this._fire({...this._config, card_style: e.target.value});
      });
    }
    this.shadowRoot.querySelector("#sel-lang").addEventListener("change", e => {
      this._fire({...this._config, language: e.target.value});
    });
    const windUnitSel = this.shadowRoot.querySelector("#sel-wind-unit");
    if (windUnitSel) {
      windUnitSel.addEventListener("change", e => {
        this._fire({...this._config, wind_unit: e.target.value});
      });
    }
    this._setupWindEntityPicker();
    this.shadowRoot.querySelectorAll("ha-switch[data-key]").forEach(el => {
      el.addEventListener("change", () => {
        this._fire({...this._config, [el.dataset.key]: el.checked});
      });
    });

    const alphaSlider = this.shadowRoot.querySelector("#theme-alpha-slider");
    const alphaLbl    = this.shadowRoot.querySelector("#theme-alpha-lbl");
    if (alphaSlider) {
      alphaSlider.addEventListener("input", e => {
        if (alphaLbl) alphaLbl.textContent = `${e.target.value}%`;
      });
      alphaSlider.addEventListener("change", e => {
        this._fire({...this._config, theme_alpha: parseInt(e.target.value, 10)});
      });
    }

    const bgText    = this.shadowRoot.querySelector("#bg-text");
    const bgPicker  = this.shadowRoot.querySelector("#bg-color-picker");
    const bgPreview = this.shadowRoot.querySelector("#bg-preview");
    if (bgText) {
      bgText.addEventListener("change", e => {
        const val = e.target.value.trim();
        if (bgPreview) bgPreview.style.background = val;
        this._fire({...this._config, custom_bg: val});
      });
    }
    if (bgPicker) {
      bgPicker.addEventListener("input", e => {
        const val = e.target.value;
        if (bgPreview) bgPreview.style.background = val;
        if (bgText)    bgText.value = val;
        this._config = {...this._config, custom_bg: val};
        this._applyBgToCard(val);
      });
      bgPicker.addEventListener("change", e => {
        const val = e.target.value;
        if (bgPreview) bgPreview.style.background = val;
        if (bgText)    bgText.value = val;
        this._fire({...this._config, custom_bg: val});
      });
    }
  }

  _setupWindEntityPicker() {
    const container = this.shadowRoot?.querySelector("#wind-entity-picker");
    if (!container || !this._hass) return;

    container.innerHTML = "";
    const picker = document.createElement("ha-entity-picker");
    picker.hass = this._hass;
    picker.value = this._config.entity_wind_speed || "";
    picker.includeDomains = ["sensor"];
    picker.includeDeviceClasses = ["wind_speed"];
    picker.allowCustomEntity = true;
    const onPickerChange = (e) => {
      const val = e.detail?.value ?? "";
      this._fire({...this._config, entity_wind_speed: val || ""});
    };
    picker.addEventListener("value-changed", onPickerChange);
    picker.addEventListener("changed", onPickerChange);
    container.appendChild(picker);
  }

  _syncPickers() {
    this.shadowRoot?.querySelectorAll("ha-entity-picker").forEach(p => {
      if (this._hass) p.hass = this._hass;
    });
  }

  _toggle(id, label, hint, checked) {
    const keyMap = {
      "sw-wind":      "show_wind",
      "sw-sager":     "show_sager",
      "sw-precip":    "show_precip",
      "sw-forecasts": "show_forecasts",
      "sw-auto-theme":"auto_theme",
      "sw-trend":     "show_trend",
      "sw-history":   "show_history",
      "sw-subdial":   "show_subdial",
    };
    return `<div class="row">
      <div>
        <div class="row-label">${label}</div>
        <div class="row-hint">${hint}</div>
      </div>
      <ha-switch data-key="${keyMap[id]}" ${checked?"checked":""}></ha-switch>
    </div>`;
  }
}

if (!customElements.get("zambretti-weather-card-editor")) {
  customElements.define("zambretti-weather-card-editor", ZambrettiWeatherCardEditor);
}

export { ZambrettiWeatherCardEditor };

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    objectName: "playwrightScriptsRunner"
    title: "Прогон скриптов Playwright - Chrome Profile Manager"
    color: "#f5f5f5"
    
    // Устанавливаем фиксированный размер окна
    width: 1000
    height: 700
    
    // Центрируем окно на экране
    x: Screen.width / 2 - width / 2
    y: Screen.height / 2 - height / 2
    
    // Флаг для отслеживания видимости окна
    property bool isVisible: false
    
    // Переопределяем метод show для установки флага
    function show() {
        isVisible = true
        visible = true
        
        // Обновляем список скриптов Playwright
        try {
            profileManager.update_playwright_scripts_list()
            console.log("Метод update_playwright_scripts_list() выполнен успешно")
        } catch (e) {
            console.log("Ошибка при вызове update_playwright_scripts_list():", e)
        }
        
        // Обновляем список профилей при открытии окна
        profileManager.update_profiles_list()
        
        // Сбрасываем выбранные профили и скрипты
        profileManager.deselectAllProfiles()
        resetScriptSelection()
        
        // Обновляем UI
        updateSelectedProfiles()
        updateSelectedScripts()
    }
    
    // Переопределяем метод hide для установки флага
    function hide() {
        isVisible = false
        visible = false
    }
    
    // Обработка закрытия окна
    onClosing: function(close) {
        // Вместо закрытия просто скрываем окно
        hide()
        close.accepted = false
    }
    
    signal backClicked()
    
    // Состояние операций
    property bool isProcessing: false
    property string operationStatus: ""
    property bool operationSuccess: false
    
    // Модели для списков
    property var selectedProfiles: []
    property var selectedScripts: []
    property bool useHeadlessMode: false
    
    // Текущий способ выбора профилей
    property string currentSelectionMethod: "list"
    
    // Функция для сброса выбора скриптов
    function resetScriptSelection() {
        for (var i = 0; i < scriptsListView.count; i++) {
            var item = scriptsListView.itemAtIndex(i)
            if (item) {
                item.children[0].checked = false
            }
        }
        selectedScripts = []
    }
    
    // Обработка сигналов от ProfileManager
    Connections {
        target: profileManager
        
        function onPlaywrightScriptOperationStatusChanged(success, message) {
            console.log("Получен сигнал onPlaywrightScriptOperationStatusChanged:", success, message)
            
            // Отображаем сообщение о статусе
            operationSuccess = success
            operationStatus = message
            statusMessage.visible = true
            statusTimer.restart()
            
            // Сбрасываем флаг выполнения скриптов
            isProcessing = false
            console.log("Флаг isProcessing сброшен в false")
            
            // Обновляем цвет кнопки
            if (selectedProfiles.length > 0 && selectedScripts.length > 0) {
                runButtonRect.color = "#4CAF50"
            } else {
                runButtonRect.color = "#e0e0e0"
            }
        }
        
        function onPlaywrightScriptsListChanged() {
            console.log("Получен сигнал onPlaywrightScriptsListChanged")
            console.log("Скрипты:", profileManager.playwrightScriptsList)
        }
        
        function onProfilesListChanged() {
            console.log("Получен сигнал onProfilesListChanged")
            // При изменении списка профилей обновляем выбранные профили
            updateSelectedProfiles()
            // Обновляем модель для ListView
            selectedProfilesListView.model = Qt.binding(function() {
                var result = []
                for (var i = 0; i < profileManager.profilesList.length; i++) {
                    var profile = profileManager.profilesList[i]
                    if (profileManager.isProfileSelected(profile)) {
                        result.push(profile)
                    }
                }
                return result
            })
        }
        
        function onSelectedProfilesChanged() {
            // Обновляем список выбранных профилей
            updateSelectedProfiles()
        }
    }
    
    // Функция для обновления списка выбранных профилей
    function updateSelectedProfiles() {
        selectedProfiles = []
        for (var i = 0; i < profileManager.profilesList.length; i++) {
            var profile = profileManager.profilesList[i]
            if (profileManager.isProfileSelected(profile)) {
                selectedProfiles.push(profile)
            }
        }
        console.log("Обновлены выбранные профили:", JSON.stringify(selectedProfiles))
        
        // Проверяем состояние кнопки запуска
        console.log("Кнопка запуска должна быть активна:", selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing)
        console.log("Выбрано профилей:", selectedProfiles.length)
        console.log("Выбрано скриптов:", selectedScripts.length)
    }
    
    // Функция для обновления списка выбранных скриптов
    function updateSelectedScripts() {
        selectedScripts = []
        for (var i = 0; i < scriptsListView.count; i++) {
            var item = scriptsListView.itemAtIndex(i)
            if (item && item.children[0].checked) {
                // Используем модель ListView напрямую
                selectedScripts.push(scriptsListView.model[i])
            }
        }
        console.log("Обновлены выбранные скрипты:", JSON.stringify(selectedScripts))
        
        // Проверяем состояние кнопки запуска
        console.log("Кнопка запуска должна быть активна:", selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing)
        console.log("Выбрано профилей:", selectedProfiles.length)
        console.log("Выбрано скриптов:", selectedScripts.length)
    }
    
    Component.onCompleted: {
        // Загружаем список профилей при создании компонента
        console.log("Компонент создан, загружаем данные")
        profileManager.update_profiles_list()
        updateSelectedProfiles()
        updateSelectedScripts()
    }
    
    // Модели для списков
    ListModel {
        id: scriptsListModel
    }
    
    // Таймер для скрытия сообщения о статусе
    Timer {
        id: statusTimer
        interval: 5000
        onTriggered: statusMessage.visible = false
    }
    
    // Основной контейнер
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        // Заголовок
        Text {
            text: "Прогон скриптов Playwright"
            font.pixelSize: 24
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }
        
        // Основной контейнер с двумя колонками
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15
            
            // Левая колонка - Способы выбора профилей
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.3
                color: "#ffffff"
                border.color: "#e0e0e0"
                border.width: 1
                radius: 4
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок
                    Text {
                        text: "Выбор профилей"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Переключатель способа выбора профилей
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        
                        Button {
                            text: "По списку"
                            Layout.fillWidth: true
                            highlighted: currentSelectionMethod === "list"
                            onClicked: {
                                currentSelectionMethod = "list"
                            }
                        }
                        
                        Button {
                            text: "По комментарию"
                            Layout.fillWidth: true
                            highlighted: currentSelectionMethod === "comment"
                            onClicked: {
                                currentSelectionMethod = "comment"
                            }
                        }
                        
                        Button {
                            text: "По имени"
                            Layout.fillWidth: true
                            highlighted: currentSelectionMethod === "name"
                            onClicked: {
                                currentSelectionMethod = "name"
                            }
                        }
                    }
                    
                    // Кнопки для выбора профилей
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Выбрать профили"
                            Layout.fillWidth: true
                            onClicked: {
                                if (currentSelectionMethod === "list") {
                                    // Открываем окно выбора списка профилей
                                    profileManager.selectFromList()
                                } else if (currentSelectionMethod === "comment") {
                                    // Открываем окно выбора по комментарию
                                    profileManager.selectByComment()
                                } else if (currentSelectionMethod === "name") {
                                    // Открываем окно выбора по имени
                                    profileManager.enterNames()
                                }
                            }
                        }
                        
                        Button {
                            text: "Выбрать все"
                            Layout.fillWidth: true
                            onClicked: {
                                profileManager.selectAll()
                            }
                        }
                    }
                    
                    // Чекбокс "Выбрать все профили"
                    CheckBox {
                        id: selectAllCheckbox
                        text: "Выбрать все профили"
                        Layout.fillWidth: true
                        onCheckedChanged: {
                            if (checked) {
                                profileManager.selectAll()
                            } else {
                                profileManager.deselectAllProfiles()
                            }
                        }
                    }
                    
                    // Список всех профилей с чекбоксами
                    Text {
                        text: "Доступные профили:"
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    ListView {
                        id: profilesListView
                        Layout.fillWidth: true
                        Layout.preferredHeight: 150
                        clip: true
                        
                        model: profileManager.profilesList
                        
                        delegate: Item {
                            width: profilesListView.width
                            height: 30
                            
                            CheckBox {
                                id: profileCheckBox
                                anchors.fill: parent
                                text: modelData
                                font.pixelSize: 14
                                checked: profileManager.isProfileSelected(modelData)
                                
                                onCheckedChanged: {
                                    if (checked !== profileManager.isProfileSelected(modelData)) {
                                        profileManager.toggleProfileSelection(modelData, checked)
                                        // Принудительно обновляем список выбранных профилей
                                        updateSelectedProfiles()
                                    }
                                }
                            }
                            
                            // Обработчик изменения состояния выбранных профилей
                            Connections {
                                target: profileManager
                                function onSelectedProfilesChanged() {
                                    // Обновляем состояние чекбокса в соответствии с выбором профиля
                                    profileCheckBox.checked = profileManager.isProfileSelected(modelData)
                                }
                            }
                        }
                    }
                    
                    // Список выбранных профилей
                    Text {
                        text: "Выбранные профили:"
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    ListView {
                        id: selectedProfilesListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        model: {
                            var result = []
                            for (var i = 0; i < profileManager.profilesList.length; i++) {
                                var profile = profileManager.profilesList[i]
                                if (profileManager.isProfileSelected(profile)) {
                                    result.push(profile)
                                }
                            }
                            return result
                        }
                        
                        delegate: Rectangle {
                            width: selectedProfilesListView.width
                            height: 30
                            color: index % 2 === 0 ? "#f9f9f9" : "#ffffff"
                            
                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 5
                                verticalAlignment: Text.AlignVCenter
                                text: modelData
                                elide: Text.ElideRight
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    profileManager.toggleProfileSelection(modelData, false)
                                }
                            }
                        }
                    }
                    
                    // Кнопка очистки выбора
                    Button {
                        text: "Очистить выбор"
                        Layout.fillWidth: true
                        onClicked: {
                            profileManager.deselectAllProfiles()
                        }
                    }
                }
            }
            
            // Правая колонка - Выбор скриптов и запуск
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "#ffffff"
                border.color: "#e0e0e0"
                border.width: 1
                radius: 4
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок
                    Text {
                        text: "Выбор скриптов"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Список скриптов с чекбоксами
                    ListView {
                        id: scriptsListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        // Используем profileManager.playwrightScriptsList вместо локального списка
                        model: profileManager.playwrightScriptsList || ["test_script"]
                        
                        // Полностью новый делегат
                        delegate: Item {
                            width: scriptsListView.width
                            height: 30
                            
                            CheckBox {
                                anchors.fill: parent
                                text: modelData
                                
                                onCheckedChanged: {
                                    updateSelectedScripts()
                                    
                                    // Обновляем цвет кнопки запуска
                                    if (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) {
                                        runButtonRect.color = "#4CAF50"
                                    } else {
                                        runButtonRect.color = "#e0e0e0"
                                    }
                                }
                            }
                        }
                    }
                    
                    // Кнопки для выбора скриптов
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Выбрать все"
                            Layout.fillWidth: true
                            onClicked: {
                                for (var i = 0; i < scriptsListView.count; i++) {
                                    var item = scriptsListView.itemAtIndex(i)
                                    if (item) {
                                        item.children[0].checked = true
                                    }
                                }
                            }
                        }
                        
                        Button {
                            text: "Очистить выбор"
                            Layout.fillWidth: true
                            onClicked: {
                                resetScriptSelection()
                            }
                        }
                    }
                    
                    // Опции запуска
                    CheckBox {
                        id: headlessCheckBox
                        text: "Headless режим"
                        checked: useHeadlessMode
                        onCheckedChanged: {
                            useHeadlessMode = checked
                        }
                    }
                    
                    // Кнопка запуска
                    Rectangle {
                        id: runButtonRect
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        color: "#e0e0e0"  // Изначально серая, пока не выбраны профили и скрипты
                        radius: 4
                        
                        Text {
                            anchors.centerIn: parent
                            text: isProcessing ? "Выполняется..." : "Запустить скрипты"
                            font.pixelSize: 16
                            font.bold: true
                            color: "#ffffff"
                        }
                        
                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                if (!isProcessing && selectedProfiles.length > 0 && selectedScripts.length > 0) {
                                    isProcessing = true
                                    runButtonRect.color = "#cccccc"
                                    
                                    // Запускаем скрипты
                                    profileManager.runPlaywrightScripts(selectedProfiles, selectedScripts, useHeadlessMode)
                                }
                            }
                        }
                    }
                    
                    // Сообщение о статусе
                    Rectangle {
                        id: statusMessage
                        Layout.fillWidth: true
                        Layout.preferredHeight: 50
                        color: operationSuccess ? "#4CAF50" : "#F44336"
                        radius: 4
                        visible: false
                        
                        Text {
                            anchors.fill: parent
                            anchors.margins: 10
                            text: operationStatus
                            color: "#ffffff"
                            wrapMode: Text.WordWrap
                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }
        }
        
        // Кнопка "Назад"
        Button {
            text: "Назад"
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 40
            
            onClicked: {
                hide()
                backClicked()
            }
        }
    }
} 
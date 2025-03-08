import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    objectName: "managerScriptsRunner"
    title: "Прогон скриптов Manager - Chrome Profile Manager"
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
        
        // Обновляем список скриптов менеджера
        try {
            profileManager.update_manager_scripts_list()
            console.log("Метод update_manager_scripts_list() выполнен успешно")
        } catch (e) {
            console.log("Ошибка при вызове update_manager_scripts_list():", e)
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
    property bool shuffleScripts: false
    
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
        
        function onManagerScriptOperationStatusChanged(success, message) {
            isProcessing = false
            operationStatus = message
            operationSuccess = success
            statusMessage.visible = true
            statusTimer.restart()
            
            console.log("===== ОПЕРАЦИЯ ВЫПОЛНЕНИЯ СКРИПТОВ ЗАВЕРШЕНА =====")
            console.log("Успех:", success)
            console.log("Сообщение:", message)
            console.log("Флаг isProcessing сброшен в false")
            
            // Обновляем цвет кнопки
            if (selectedProfiles.length > 0 && selectedScripts.length > 0) {
                runButtonRect.color = "#4CAF50"
            } else {
                runButtonRect.color = "#e0e0e0"
            }
        }
        
        function onSelectedProfilesChanged() {
            // Обновляем список выбранных профилей
            updateSelectedProfiles()
        }
        
        function onProfilesListChanged() {
            // При изменении списка профилей обновляем выбранные профили
            updateSelectedProfiles()
        }
        
        function onManagerScriptsListChanged() {
            // При изменении списка скриптов обновляем UI
            console.log("Список скриптов менеджера изменился")
        }
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
        
        // Обновляем состояние чекбокса "Выбрать все профили"
        var allSelected = selectedProfiles.length === profileManager.profilesList.length && profileManager.profilesList.length > 0
        if (selectAllCheckbox.checked !== allSelected) {
            selectAllCheckbox.checked = allSelected
            console.log("Обновлен чекбокс 'Выбрать все профили':", allSelected)
        }
        
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
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        // Заголовок
        Text {
            text: "Прогон скриптов Manager"
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
                border.color: "#d0d0d0"
                radius: 5
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок секции
                    Text {
                        text: "Способ выбора профилей"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Кнопки выбора способа
                    Button {
                        text: "📋 Выбрать из списка"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: currentSelectionMethod === "list" ? "#e0e0e0" : (parent.hovered ? "#f0f0f0" : "#ffffff")
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 14
                            elide: Text.ElideNone
                        }
                        
                        onClicked: {
                            currentSelectionMethod = "list"
                            profileManager.deselectAllProfiles()
                        }
                    }
                    
                    Button {
                        text: "✏️ Вписать названия"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: currentSelectionMethod === "names" ? "#e0e0e0" : (parent.hovered ? "#f0f0f0" : "#ffffff")
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 14
                            elide: Text.ElideNone
                        }
                        
                        onClicked: {
                            currentSelectionMethod = "names"
                            profileManager.deselectAllProfiles()
                        }
                    }
                    
                    Button {
                        text: "🔍 Выбрать по комментарию"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        
                        background: Rectangle {
                            color: currentSelectionMethod === "comment" ? "#e0e0e0" : (parent.hovered ? "#f0f0f0" : "#ffffff")
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        contentItem: Text {
                            text: parent.text
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 14
                            elide: Text.ElideNone
                        }
                        
                        onClicked: {
                            currentSelectionMethod = "comment"
                            profileManager.deselectAllProfiles()
                        }
                    }
                    
                    // Чекбокс для выбора всех профилей
                    CheckBox {
                        id: selectAllCheckbox
                        text: "Выбрать все профили"
                        Layout.fillWidth: true
                        
                        onCheckedChanged: {
                            if (checked) {
                                profileManager.selectAllProfiles()
                            } else {
                                profileManager.deselectAllProfiles()
                            }
                            // Принудительно обновляем список выбранных профилей
                            updateSelectedProfiles()
                            // Принудительно обновляем состояние чекбоксов в списке профилей
                            profilesListView.forceLayout()
                            
                            // Добавляем логирование для отладки
                            console.log("Чекбокс 'Выбрать все профили' изменен на:", checked)
                            console.log("Количество выбранных профилей после изменения:", selectedProfiles.length)
                        }
                    }
                    
                    // Чекбокс для перемешивания скриптов
                    CheckBox {
                        id: shuffleScriptsCheckbox
                        text: "Перемешать порядок скриптов"
                        Layout.fillWidth: true
                        
                        onCheckedChanged: {
                            shuffleScripts = checked
                        }
                    }
                    
                    // Информация о выбранных профилях
                    Text {
                        text: "Выбрано профилей: " + selectedProfiles.length
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                    
                    // Растягивающийся элемент для заполнения пространства
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
            
            // Центральная колонка - Выбор профилей (зависит от способа)
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.3
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 5
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок секции
                    Text {
                        text: currentSelectionMethod === "list" ? "Выбор профилей из списка" : 
                              currentSelectionMethod === "names" ? "Ввод названий профилей" : 
                              "Поиск по комментарию"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Содержимое в зависимости от способа выбора
                    StackLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentIndex: currentSelectionMethod === "list" ? 0 : 
                                     currentSelectionMethod === "names" ? 1 : 2
                        
                        // Список профилей с чекбоксами
                        ListView {
                            id: profilesListView
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
                        
                        // Ввод названий профилей
                        ColumnLayout {
                            spacing: 10
                            
                            TextArea {
                                id: profileNamesInput
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                placeholderText: "Введите названия профилей, по одному на строку"
                                wrapMode: TextEdit.Wrap
                                font.pixelSize: 14
                            }
                            
                            Button {
                                text: "Применить"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                
                                background: Rectangle {
                                    color: parent.hovered ? "#e0e0e0" : "#f5f5f5"
                                    border.color: "#d0d0d0"
                                    radius: 3
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 14
                                    elide: Text.ElideNone
                                }
                                
                                onClicked: {
                                    // Разбиваем текст на строки и выбираем профили
                                    var profileNames = profileNamesInput.text.split("\n").filter(function(name) {
                                        return name.trim() !== "";
                                    });
                                    
                                    profileManager.deselectAllProfiles();
                                    
                                    for (var i = 0; i < profileNames.length; i++) {
                                        var name = profileNames[i].trim();
                                        if (profileManager.profilesList.includes(name)) {
                                            profileManager.toggleProfileSelection(name, true);
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Поиск по комментарию
                        ColumnLayout {
                            spacing: 10
                            
                            TextField {
                                id: commentSearchInput
                                Layout.fillWidth: true
                                placeholderText: "Введите текст для поиска в комментариях"
                                font.pixelSize: 14
                            }
                            
                            Button {
                                text: "Найти"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                
                                background: Rectangle {
                                    color: parent.hovered ? "#e0e0e0" : "#f5f5f5"
                                    border.color: "#d0d0d0"
                                    radius: 3
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 14
                                    elide: Text.ElideNone
                                }
                                
                                onClicked: {
                                    // Ищем профили по комментарию
                                    profileManager.searchProfilesByComment(commentSearchInput.text);
                                }
                            }
                            
                            // Список найденных профилей
                            ListView {
                                id: filteredProfilesListView
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                
                                model: profileManager.filteredProfilesList
                                
                                delegate: CheckBox {
                                    width: filteredProfilesListView.width
                                    height: 30
                                    text: modelData
                                    font.pixelSize: 14
                                    checked: profileManager.isProfileSelected(modelData)
                                    
                                    onCheckedChanged: {
                                        profileManager.toggleProfileSelection(modelData, checked)
                                        // Принудительно обновляем список выбранных профилей
                                        updateSelectedProfiles()
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Правая колонка - Выбор скриптов
            Rectangle {
                Layout.fillHeight: true
                Layout.fillWidth: true
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 5
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок секции
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
                        
                        // Используем profileManager.managerScriptsList вместо локального списка
                        model: profileManager.managerScriptsList || ["test_script"]
                        
                        // Полностью новый делегат
                        delegate: Item {
                            width: scriptsListView.width
                            height: 30
                            
                            CheckBox {
                                id: scriptCheckBox
                                anchors.fill: parent
                                text: modelData
                                font.pixelSize: 14
                                
                                onCheckedChanged: {
                                    console.log("Скрипт " + modelData + " " + (checked ? "выбран" : "отменен"))
                                    root.updateSelectedScripts()
                                }
                            }
                        }
                    }
                    
                    // Информация о выбранных скриптах
                    Text {
                        text: "Выбрано скриптов: " + selectedScripts.length
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                }
            }
        }
        
        // Панель управления
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#ffffff"
            border.color: "#d0d0d0"
            radius: 5
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 15
                
                // Кнопка запуска скриптов
                Rectangle {
                    id: runButtonRect
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    color: (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) ? "#4CAF50" : "#e0e0e0"
                    radius: 3
                    border.color: "#d0d0d0"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Запустить скрипты"
                        color: (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) ? "white" : "#999999"
                        font.pixelSize: 14
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        
                        onEntered: {
                            if (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) {
                                parent.color = "#45a049" // Темно-зеленый при наведении
                            }
                        }
                        
                        onExited: {
                            if (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) {
                                parent.color = "#4CAF50" // Возвращаем обычный зеленый
                            }
                        }
                        
                        onClicked: {
                            console.log("===== КНОПКА ЗАПУСКА СКРИПТОВ НАЖАТА =====")
                            console.log("Выбранные профили:", JSON.stringify(selectedProfiles))
                            console.log("Выбранные скрипты:", JSON.stringify(selectedScripts))
                            console.log("Состояние isProcessing:", isProcessing)
                            
                            if (selectedProfiles.length > 0 && selectedScripts.length > 0 && !isProcessing) {
                                isProcessing = true
                                
                                // Обновляем цвет кнопки
                                parent.color = "#e0e0e0"
                                
                                console.log("===== ЗАПУСКАЮ СКРИПТЫ =====")
                                console.log("Скрипты:", JSON.stringify(selectedScripts))
                                console.log("Профили:", JSON.stringify(selectedProfiles))
                                console.log("Перемешать скрипты:", shuffleScripts)
                                console.log("Флаг isProcessing установлен в true")
                                
                                // Запускаем скрипты
                                try {
                                    // Явно передаем выбранные профили в ProfileManager
                                    profileManager.setSelectedProfiles(selectedProfiles)
                                    profileManager.runManagerScripts(selectedProfiles, selectedScripts, shuffleScripts)
                                    console.log("===== МЕТОД runManagerScripts ВЫЗВАН =====")
                                } catch (e) {
                                    console.log("===== ОШИБКА ПРИ ВЫЗОВЕ runManagerScripts =====", e)
                                    isProcessing = false
                                    
                                    // Восстанавливаем цвет кнопки
                                    if (selectedProfiles.length > 0 && selectedScripts.length > 0) {
                                        parent.color = "#4CAF50"
                                    } else {
                                        parent.color = "#e0e0e0"
                                    }
                                    
                                    // Показываем сообщение об ошибке
                                    operationSuccess = false
                                    operationStatus = "Ошибка при запуске скриптов: " + e
                                    statusMessage.visible = true
                                    statusTimer.restart()
                                }
                            } else {
                                console.log("===== НЕВОЗМОЖНО ЗАПУСТИТЬ СКРИПТЫ =====")
                                console.log("Не выбраны профили или скрипты, или уже идет обработка")
                                console.log("selectedProfiles.length:", selectedProfiles.length)
                                console.log("selectedScripts.length:", selectedScripts.length)
                                console.log("isProcessing:", isProcessing)
                            }
                        }
                    }
                }
            }
        }
        
        // Сообщение о статусе
        Rectangle {
            id: statusMessage
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            Layout.topMargin: 10
            property bool success: operationSuccess
            property string message: operationStatus
            
            color: success ? "#e6f7e6" : "#ffebee"  // Зеленый для успеха, красный для ошибки
            border.color: success ? "#c3e6c3" : "#ffcdd2"
            radius: 5
            visible: false
            
            Text {
                anchors.centerIn: parent
                text: statusMessage.message
                color: statusMessage.success ? "#2e7d32" : "#c62828"  // Темно-зеленый или темно-красный для текста
                font.pixelSize: 14
                width: parent.width - 20
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            
            // Таймер для скрытия сообщения
            Timer {
                id: statusTimer
                interval: 3000  // 3 секунды
                onTriggered: statusMessage.visible = false
            }
        }
        
        // Кнопка "Закрыть"
        Button {
            text: "🏠 Закрыть окно"
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            flat: true
            enabled: !isProcessing
            
            background: Rectangle {
                color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                border.color: "#d0d0d0"
                radius: 3
            }
            
            contentItem: Text {
                text: parent.text
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 14
                color: parent.enabled ? "#000000" : "#999999"
                elide: Text.ElideNone
            }
            
            onClicked: {
                root.hide()
                root.backClicked()
            }
        }
    }
} 
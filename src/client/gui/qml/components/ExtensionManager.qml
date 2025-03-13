import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    title: "Управление расширениями - Chrome Profile Manager"
    color: "#f5f5f5"
    
    // Устанавливаем фиксированный размер окна
    width: 1200
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
    
    // Состояние операций с расширениями
    property bool isProcessing: false
    property string operationStatus: ""
    property bool operationSuccess: false
    
    // Модели для списков
    property var defaultExtensionsModel: []
    property var selectedExtensions: []
    property var selectedProfiles: []
    
    // Источник текущего списка расширений (default или profile_name)
    property string currentExtensionsSource: "default"
    
    // Обработка сигналов от ProfileManager
    Connections {
        target: profileManager
        
        function onExtensionOperationStatusChanged(success, message) {
            isProcessing = false
            operationStatus = message
            operationSuccess = success
            statusMessage.visible = true
            statusTimer.restart()
        }
        
        function onExtensionsListChanged(extensions) {
            console.log("Получен новый список расширений:", JSON.stringify(extensions))
            defaultExtensionsModel = extensions
            // Сбрасываем выбранные расширения при обновлении списка
            selectedExtensions = []
            // Обновляем счетчики
            updateSelectedExtensions()
            updateSelectedProfiles()
        }
        
        function onSelectedProfilesChanged() {
            // Обновляем список выбранных профилей
            updateSelectedProfiles()
            // Проверяем активность кнопок
            checkButtonsState()
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
        // Проверяем активность кнопок
        checkButtonsState()
    }
    
    // Функция для обновления списка выбранных расширений
    function updateSelectedExtensions() {
        selectedExtensions = []
        for (var i = 0; i < extensionsListView.count; i++) {
            var item = extensionsListView.itemAtIndex(i)
            if (item && item.checked) {
                selectedExtensions.push(defaultExtensionsModel[i].id)
            }
        }
        console.log("Обновлены выбранные расширения:", JSON.stringify(selectedExtensions))
        // Проверяем активность кнопок
        checkButtonsState()
    }
    
    // Функция для проверки состояния кнопок
    function checkButtonsState() {
        var shouldBeEnabled = selectedExtensions.length > 0 && selectedProfiles.length > 0 && !isProcessing
        console.log("Кнопка должна быть активна:", shouldBeEnabled)
        console.log("Выбрано расширений:", selectedExtensions.length)
        console.log("Выбрано профилей:", selectedProfiles.length)
        console.log("isProcessing:", isProcessing)
        
        // Принудительно обновляем состояние кнопок
        installButton.enabled = shouldBeEnabled
        removeButton.enabled = shouldBeEnabled
    }
    
    Component.onCompleted: {
        // Загружаем список расширений и профилей при создании компонента
        console.log("Компонент создан, загружаем данные")
        currentExtensionsSource = "default"
        profileManager.getDefaultExtensionsList()
        updateSelectedProfiles()
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        // Заголовок
        Text {
            text: "Управление расширениями"
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
            
            // Левая колонка - Профили
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.35
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 5
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    // Заголовок секции профилей
                    Text {
                        text: "Профили"
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Кнопки выбора всех/снятия выбора
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Выбрать все"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            
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
                                profileManager.selectAllProfiles()
                                updateSelectedProfiles()
                            }
                        }
                        
                        Button {
                            text: "Снять выбор"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            
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
                                profileManager.deselectAllProfiles()
                                updateSelectedProfiles()
                            }
                        }
                    }
                    
                    // Список профилей с чекбоксами
                    ListView {
                        id: profilesListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        model: profileManager.profilesList
                        
                        delegate: CheckBox {
                            width: profilesListView.width
                            height: 30
                            text: modelData
                            font.pixelSize: 14
                            checked: profileManager.isProfileSelected(modelData)
                            
                            onCheckedChanged: {
                                profileManager.toggleProfileSelection(modelData, checked)
                                updateSelectedProfiles()
                            }
                        }
                    }
                    
                    // Информация о выбранных профилях
                    Text {
                        text: "Выбрано профилей: " + selectedProfiles.length
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                    
                    // Кнопка для получения расширений из профиля 0
                    Button {
                        text: "Из профиля 0"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        
                        background: Rectangle {
                            color: parent.hovered ? "#e0e0e0" : "#f5f5f5"
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        onClicked: {
                            // Получаем список расширений из профиля 0
                            currentExtensionsSource = "0"
                            profileManager.getProfileExtensions("0")
                        }
                    }
                    
                    // Кнопка для копирования выбранных расширений из профиля 0 в default_extensions
                    Button {
                        text: "Копировать выбранные в дефолтные"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        visible: currentExtensionsSource === "0" && selectedExtensions.length > 0
                        
                        background: Rectangle {
                            color: parent.hovered ? "#e0e0e0" : "#f5f5f5"
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        onClicked: {
                            // Копируем выбранные расширения из профиля 0 в default_extensions
                            for (var i = 0; i < selectedExtensions.length; i++) {
                                profileManager.copyExtensionFromProfileToDefault("0", selectedExtensions[i])
                            }
                        }
                    }
                    
                    // Кнопка для копирования всех расширений из профиля 0 в default_extensions
                    Button {
                        text: "Копировать все в дефолтные"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        visible: currentExtensionsSource === "0"
                        
                        background: Rectangle {
                            color: parent.hovered ? "#e0e0e0" : "#f5f5f5"
                            border.color: "#d0d0d0"
                            radius: 3
                        }
                        
                        onClicked: {
                            // Копируем все расширения из профиля 0 в default_extensions
                            profileManager.copyAllExtensionsFromProfileToDefault("0")
                        }
                    }
                    
                    // Кнопка для возврата к списку дефолтных расширений
                    Button {
                        text: "Вернуться к дефолтным расширениям"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        
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
                            // Возвращаемся к списку дефолтных расширений
                            currentExtensionsSource = "default"
                            profileManager.getDefaultExtensionsList()
                        }
                    }
                    
                    // Кнопка для копирования расширений из профиля в дефолтные
                    Button {
                        text: "Копировать расширения из профиля 0 в дефолтные"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        visible: true
                        
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
                            // Копируем выбранные расширения из профиля 0 в дефолтные
                            for (var i = 0; i < selectedExtensions.length; i++) {
                                profileManager.copyExtensionFromProfileToDefault("0", selectedExtensions[i])
                            }
                        }
                    }
                    
                    // Кнопка для копирования всех расширений из профиля 0 в дефолтные
                    Button {
                        text: "Копировать все расширения из профиля 0 в дефолтные"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30
                        
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
                            // Копируем все расширения из профиля 0 в дефолтные
                            profileManager.copyAllExtensionsFromProfileToDefault("0")
                        }
                    }
                }
            }
            
            // Правая колонка - Расширения
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
                    
                    // Заголовок секции расширений
                    Text {
                        text: currentExtensionsSource === "default" ? 
                              "Доступные расширения (дефолтные)" : 
                              "Расширения из профиля " + currentExtensionsSource
                        font.pixelSize: 18
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Кнопки выбора всех/снятия выбора
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Выбрать все"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            
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
                                for (var i = 0; i < extensionsListView.count; i++) {
                                    var item = extensionsListView.itemAtIndex(i)
                                    if (item) {
                                        item.checked = true
                                    }
                                }
                                updateSelectedExtensions()
                            }
                        }
                        
                        Button {
                            text: "Снять выбор"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 30
                            
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
                                for (var i = 0; i < extensionsListView.count; i++) {
                                    var item = extensionsListView.itemAtIndex(i)
                                    if (item) {
                                        item.checked = false
                                    }
                                }
                                updateSelectedExtensions()
                            }
                        }
                    }
                    
                    // Список расширений с чекбоксами
                    ListView {
                        id: extensionsListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        model: defaultExtensionsModel
                        
                        delegate: Item {
                            width: extensionsListView.width
                            height: 60
                            property bool checked: false
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 5
                                anchors.rightMargin: 5
                                spacing: 10
                                
                                CheckBox {
                                    id: extensionCheckbox
                                    checked: parent.parent.checked
                                    onCheckedChanged: {
                                        parent.parent.checked = checked
                                        updateSelectedExtensions()
                                    }
                                }
                                
                                // Иконка расширения
                                Rectangle {
                                    width: 40
                                    height: 40
                                    color: "#f0f0f0"
                                    radius: 4
                                    
                                    Image {
                                        anchors.centerIn: parent
                                        source: modelData.iconUrl ? modelData.iconUrl : ""
                                        width: 32
                                        height: 32
                                        fillMode: Image.PreserveAspectFit
                                        visible: modelData.iconUrl !== "" && status === Image.Ready
                                    }
                                    
                                    // Заглушка, если иконки нет или она не загрузилась
                                    Text {
                                        anchors.centerIn: parent
                                        text: "E"
                                        font.pixelSize: 16
                                        visible: modelData.iconUrl === "" || parent.children[0].status !== Image.Ready
                                    }
                                }
                                
                                // Информация о расширении
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    
                                    Text {
                                        text: modelData.name ? modelData.name : "Без имени"
                                        font.pixelSize: 14
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: parent.width - 10
                                    }
                                    
                                    Text {
                                        text: "Версия: " + modelData.version
                                        font.pixelSize: 12
                                        color: "#666666"
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                    
                                    Text {
                                        text: "ID: " + modelData.id
                                        font.pixelSize: 10
                                        color: "#999999"
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                            
                            // Добавляем обработку клика на весь элемент для удобства выбора
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    // Инвертируем состояние чекбокса при клике на элемент
                                    parent.checked = !parent.checked
                                    extensionCheckbox.checked = parent.checked
                                }
                                z: -1 // Размещаем под другими элементами, чтобы не блокировать их взаимодействие
                            }
                            
                            // Разделительная линия
                            Rectangle {
                                width: parent.width
                                height: 1
                                color: "#e0e0e0"
                                anchors.bottom: parent.bottom
                            }
                        }
                    }
                    
                    // Информация о выбранных расширениях
                    Text {
                        text: "Выбрано расширений: " + selectedExtensions.length
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                }
            }
        }
        
        // Панель управления
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 110
            color: "#ffffff"
            border.color: "#d0d0d0"
            radius: 5
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                
                // Опция замены существующих расширений
                CheckBox {
                    id: replaceExistingCheckbox
                    text: "Заменить существующие расширения"
                    font.pixelSize: 14
                    checked: true
                    Layout.fillWidth: true
                }
                
                // Кнопки действий
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    Button {
                        id: installButton
                        text: "Установить выбранные расширения"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        enabled: selectedExtensions.length > 0 && selectedProfiles.length > 0 && !isProcessing
                        
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
                            isProcessing = true
                            console.log("Установка расширений:", JSON.stringify(selectedExtensions))
                            console.log("Для профилей:", JSON.stringify(selectedProfiles))
                            console.log("Заменять существующие:", replaceExistingCheckbox.checked)
                            
                            if (selectedProfiles.length === profileManager.profilesList.length) {
                                // Установить для всех профилей
                                profileManager.installMultipleExtensionsForAllProfiles(selectedExtensions, replaceExistingCheckbox.checked)
                            } else {
                                // Установить для выбранных профилей
                                profileManager.installMultipleExtensionsForSelectedProfiles(selectedExtensions, replaceExistingCheckbox.checked)
                            }
                            
                            // Обновляем состояние кнопок
                            checkButtonsState()
                        }
                    }
                    
                    Button {
                        id: removeButton
                        text: "Удалить выбранные расширения"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        enabled: selectedExtensions.length > 0 && selectedProfiles.length > 0 && !isProcessing
                        
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
                            isProcessing = true
                            console.log("Удаление расширений:", JSON.stringify(selectedExtensions))
                            console.log("Из профилей:", JSON.stringify(selectedProfiles))
                            
                            if (selectedProfiles.length === profileManager.profilesList.length) {
                                // Удалить из всех профилей
                                profileManager.removeMultipleExtensionsFromAllProfiles(selectedExtensions)
                            } else {
                                // Удалить из выбранных профилей
                                profileManager.removeMultipleExtensionsFromSelectedProfiles(selectedExtensions)
                            }
                            
                            // Очищаем выбранные профили
                            profileManager.deselectAllProfiles()
                            
                            // Очищаем выбранные расширения
                            for (var i = 0; i < extensionsListView.count; i++) {
                                var item = extensionsListView.itemAtIndex(i)
                                if (item && item.checked) {
                                    item.checked = false
                                }
                            }
                            selectedExtensions = []
                            
                            // Обновляем состояние кнопок
                            checkButtonsState()
                        }
                    }
                }
                
                // Кнопка запуска выбранных профилей
                Button {
                    id: launchButton
                    text: "🚀 Запустить выбранные профили"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    visible: selectedProfiles.length > 0
                    enabled: selectedProfiles.length > 0 && !isProcessing
                    
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
                        console.log("Запуск профилей:", JSON.stringify(selectedProfiles))
                        profileManager.launchProfilesByNames(selectedProfiles)
                        
                        // Очищаем выбранные профили
                        profileManager.deselectAllProfiles()
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
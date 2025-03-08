import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    objectName: "profileListManager"
    title: "Управление профилями и списками - Chrome Profile Manager"
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
        
        // Обновляем список профилей при открытии окна
        profileManager.update_profiles_list()
        
        // Обновляем список профильных списков
        profileManager.updateProfileLists()
        
        // Показываем все профили при открытии окна
        profileManager.searchProfilesByName("")
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
    
    // Состояние создания профилей
    property bool isCreating: false
    property string creationStatus: ""
    property bool creationSuccess: false
    
    // Текущий выбранный список
    property string currentListId: ""
    property string currentListName: ""
    
    // Текущая активная вкладка
    property int currentTabIndex: 0
    
    // Обработка сигналов от ProfileManager
    Connections {
        target: profileManager
        
        function onProfileListOperationStatusChanged(success, message) {
            isProcessing = false
            operationStatus = message
            operationSuccess = success
            statusMessage.visible = true
            statusTimer.restart()
        }
        
        function onProfileCreationStatusChanged(success, message) {
            isCreating = false
            creationStatus = message
            creationSuccess = success
            creationStatusMessage.visible = true
            creationStatusTimer.restart()
        }
    }
    
    // Основной макет
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10
        
        // Заголовок
        Text {
            text: "Управление профилями и списками"
            font.pixelSize: 20
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }
        
        // Вкладки
        TabBar {
            id: tabBar
            Layout.fillWidth: true
            
            TabButton {
                text: "Управление списками"
                width: implicitWidth
                onClicked: {
                    currentTabIndex = 0
                }
            }
            
            TabButton {
                text: "Создание профилей"
                width: implicitWidth
                onClicked: {
                    currentTabIndex = 1
                }
            }
        }
        
        // Стек с содержимым вкладок
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: currentTabIndex
            
            // Вкладка 1: Управление списками профилей
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                RowLayout {
                    anchors.fill: parent
                    spacing: 15
                    
                    // Левая панель - списки профилей
                    Rectangle {
                        Layout.preferredWidth: 300
                        Layout.fillHeight: true
                        color: "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 4
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            // Заголовок панели
                            Text {
                                text: "Списки профилей"
                                font.pixelSize: 16
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            
                            // Поле для создания нового списка
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 5
                                
                                TextField {
                                    id: newListNameField
                                    Layout.fillWidth: true
                                    placeholderText: "Название нового списка"
                                    
                                    background: Rectangle {
                                        color: "#ffffff"
                                        border.color: "#d0d0d0"
                                        radius: 2
                                    }
                                }
                                
                                Button {
                                    text: "Создать"
                                    Layout.preferredWidth: 80
                                    enabled: newListNameField.text.trim() !== "" && !isProcessing
                                    
                                    background: Rectangle {
                                        color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                        border.color: "#d0d0d0"
                                        radius: 2
                                    }
                                    
                                    onClicked: {
                                        isProcessing = true
                                        profileManager.createProfileList(newListNameField.text.trim())
                                        newListNameField.text = ""
                                    }
                                }
                            }
                            
                            // Список профильных списков
                            ListView {
                                id: profileListsView
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: profileManager.profileLists
                                
                                delegate: Rectangle {
                                    width: profileListsView.width
                                    height: 40
                                    color: currentListId === modelData.id ? "#e3f2fd" : (mouseArea.containsMouse ? "#f5f5f5" : "#ffffff")
                                    border.color: currentListId === modelData.id ? "#2196f3" : "#d0d0d0"
                                    border.width: currentListId === modelData.id ? 2 : 1
                                    radius: 3
                                    
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 5
                                        spacing: 5
                                        
                                        Text {
                                            text: modelData.name
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                            font.bold: currentListId === modelData.id
                                        }
                                        
                                        Text {
                                            text: "(" + modelData.profiles.length + ")"
                                            color: "#666666"
                                        }
                                        
                                        Button {
                                            text: "✏️"
                                            flat: true
                                            implicitWidth: 30
                                            implicitHeight: 30
                                            
                                            background: Rectangle {
                                                color: parent.hovered ? "#e0e0e0" : "transparent"
                                                radius: 2
                                            }
                                            
                                            onClicked: {
                                                renameDialog.listId = modelData.id
                                                renameDialog.listName = modelData.name
                                                renameDialog.open()
                                            }
                                        }
                                        
                                        Button {
                                            text: "🗑️"
                                            flat: true
                                            implicitWidth: 30
                                            implicitHeight: 30
                                            
                                            background: Rectangle {
                                                color: parent.hovered ? "#ffebee" : "transparent"
                                                radius: 2
                                            }
                                            
                                            onClicked: {
                                                deleteDialog.listId = modelData.id
                                                deleteDialog.listName = modelData.name
                                                deleteDialog.open()
                                            }
                                        }
                                    }
                                    
                                    MouseArea {
                                        id: mouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            currentListId = modelData.id
                                            currentListName = modelData.name
                                            profileManager.getProfilesInList(modelData.id)
                                        }
                                        z: -1
                                    }
                                }
                            }
                        }
                    }
                    
                    // Правая панель - профили в выбранном списке
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 4
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            // Заголовок панели
                            Text {
                                text: currentListName ? "Профили в списке: " + currentListName : "Выберите список профилей"
                                font.pixelSize: 16
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            
                            // Переключатель режима отображения
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                
                                // Кнопка "Показать все профили"
                                Button {
                                    text: "Показать все профили"
                                    Layout.fillWidth: true
                                    
                                    background: Rectangle {
                                        color: parent.hovered ? "#e0e0e0" : "#ffffff"
                                        border.color: "#d0d0d0"
                                        radius: 3
                                    }
                                    
                                    onClicked: {
                                        // Сбрасываем текущий выбранный список
                                        currentListId = ""
                                        currentListName = ""
                                        // Показываем все профили
                                        profileManager.searchProfilesByName("")
                                    }
                                }
                                
                                // Кнопка "Показать профили из списка"
                                Button {
                                    text: "Показать профили из списка"
                                    Layout.fillWidth: true
                                    enabled: currentListId !== ""
                                    
                                    background: Rectangle {
                                        color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                        border.color: "#d0d0d0"
                                        radius: 3
                                    }
                                    
                                    onClicked: {
                                        // Показываем только профили из выбранного списка
                                        profileManager.getProfilesInList(currentListId)
                                    }
                                }
                                
                                // Кнопка "Показать все для выбора"
                                Button {
                                    text: "Показать все для выбора"
                                    Layout.fillWidth: true
                                    enabled: currentListId !== ""
                                    
                                    background: Rectangle {
                                        color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                        border.color: "#d0d0d0"
                                        radius: 3
                                    }
                                    
                                    onClicked: {
                                        // Показываем все профили, но сохраняем текущий выбранный список
                                        profileManager.searchProfilesByName("")
                                    }
                                }
                            }
                            
                            // Поиск профилей
                            TextField {
                                id: profileSearchField
                                Layout.fillWidth: true
                                placeholderText: "Поиск профилей..."
                                enabled: true // Всегда активно
                                
                                background: Rectangle {
                                    color: "#ffffff"
                                    border.color: "#d0d0d0"
                                    radius: 2
                                }
                                
                                onTextChanged: {
                                    profileManager.searchProfilesByName(text)
                                }
                            }
                            
                            // Список всех профилей с чекбоксами
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#ffffff"
                                border.color: "#d0d0d0"
                                radius: 3
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 5
                                    spacing: 0
                                    
                                    // Заголовок списка профилей
                                    RowLayout {
                                        Layout.fillWidth: true
                                        height: 30
                                        spacing: 5
                                        
                                        CheckBox {
                                            id: selectAllCheckbox
                                            enabled: currentListId !== ""
                                            onCheckedChanged: {
                                                if (checked) {
                                                    profileManager.selectAllProfiles()
                                                } else {
                                                    profileManager.deselectAllProfiles()
                                                }
                                            }
                                        }
                                        
                                        Text {
                                            text: "Имя профиля"
                                            font.bold: true
                                            Layout.fillWidth: true
                                        }
                                        
                                        Text {
                                            text: "Комментарий"
                                            font.bold: true
                                            Layout.fillWidth: true
                                        }
                                    }
                                    
                                    // Список профилей
                                    ListView {
                                        id: profilesListView
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        clip: true
                                        model: profileManager.filteredProfilesList
                                        
                                        // Отладочный вывод при изменении модели
                                        onModelChanged: {
                                            console.log("Модель профилей изменилась. Количество элементов:", model.length)
                                            if (model.length > 0) {
                                                console.log("Первый элемент:", JSON.stringify(model[0]))
                                            }
                                        }
                                        
                                        delegate: Rectangle {
                                            width: profilesListView.width
                                            height: 40
                                            color: index % 2 === 0 ? "#ffffff" : "#f9f9f9"
                                            
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 5
                                                spacing: 5
                                                
                                                CheckBox {
                                                    checked: profileManager.isProfileSelected(modelData.name)
                                                    onCheckedChanged: {
                                                        profileManager.toggleProfileSelection(modelData.name, checked)
                                                    }
                                                }
                                                
                                                Text {
                                                    text: modelData.name
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                }
                                                
                                                Text {
                                                    text: modelData.comment || ""
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                    color: "#666666"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Кнопки управления профилями в списке
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                
                                // Отладочный вывод
                                Component.onCompleted: {
                                    console.log("Компонент кнопок инициализирован")
                                }
                                
                                Connections {
                                    target: profileManager
                                    function onSelectedProfilesChanged() {
                                        console.log("Выбранные профили изменились. hasSelectedProfiles:", profileManager.hasSelectedProfiles)
                                        console.log("Кнопка должна быть активна:", currentListId !== "" && profileManager.hasSelectedProfiles && !isProcessing)
                                    }
                                }
                                
                                Button {
                                    text: "Добавить выбранные профили в список"
                                    Layout.fillWidth: true
                                    enabled: currentListId !== "" && profileManager.hasSelectedProfiles && !isProcessing
                                    
                                    // Отладочный вывод при изменении состояния кнопки
                                    onEnabledChanged: {
                                        console.log("Состояние кнопки 'Добавить' изменилось. Активна:", enabled)
                                        console.log("currentListId:", currentListId)
                                        console.log("hasSelectedProfiles:", profileManager.hasSelectedProfiles)
                                        console.log("isProcessing:", isProcessing)
                                    }
                                    
                                    background: Rectangle {
                                        color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                        border.color: "#d0d0d0"
                                        radius: 3
                                    }
                                    
                                    onClicked: {
                                        isProcessing = true
                                        profileManager.addProfilesToList(currentListId)
                                    }
                                }
                                
                                Button {
                                    text: "Удалить выбранные профили из списка"
                                    Layout.fillWidth: true
                                    enabled: currentListId !== "" && profileManager.hasSelectedProfiles && !isProcessing
                                    
                                    background: Rectangle {
                                        color: parent.enabled ? (parent.hovered ? "#ffebee" : "#ffffff") : "#f5f5f5"
                                        border.color: "#d0d0d0"
                                        radius: 3
                                    }
                                    
                                    onClicked: {
                                        isProcessing = true
                                        profileManager.removeProfilesFromList(currentListId)
                                    }
                                }
                            }
                        }
                    }
                }
                
                // Сообщение о статусе для операций со списками
                Rectangle {
                    id: statusMessage
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: 40
                    property bool success: operationSuccess
                    property string message: operationStatus
                    
                    color: success ? "#e6f7e6" : "#ffebee"  // Зеленый для успеха, красный для ошибки
                    border.color: success ? "#c3e6c3" : "#ffcdd2"
                    radius: 4
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
            }
            
            // Вкладка 2: Создание профилей
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 15
                    
                    // Инструкция
                    Text {
                        text: "Выберите способ создания профилей"
                        font.pixelSize: 16
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Кнопки выбора способа создания
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "📝 Задать вручную"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            flat: true
                            enabled: !isCreating
                            
                            background: Rectangle {
                                color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                border.color: "#d0d0d0"
                                radius: 4
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                color: parent.enabled ? "#000000" : "#999999"
                            }
                            
                            onClicked: {
                                manualCreationPanel.visible = true
                                autoCreationPanel.visible = false
                            }
                        }
                        
                        Button {
                            text: "🤖 Задать автоматически"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            flat: true
                            enabled: !isCreating
                            
                            background: Rectangle {
                                color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                border.color: "#d0d0d0"
                                radius: 4
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                color: parent.enabled ? "#000000" : "#999999"
                            }
                            
                            onClicked: {
                                manualCreationPanel.visible = false
                                autoCreationPanel.visible = true
                            }
                        }
                    }
                    
                    // Панель ручного создания профилей
                    Rectangle {
                        id: manualCreationPanel
                        Layout.fillWidth: true
                        Layout.preferredHeight: 300
                        color: "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 4
                        visible: false
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 15
                            
                            Text {
                                text: "Введите имена профилей (через запятую)"
                                font.pixelSize: 14
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            
                            TextArea {
                                id: manualProfileNames
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                placeholderText: "Например: profile1, profile2, profile3"
                                wrapMode: TextEdit.Wrap
                                
                                background: Rectangle {
                                    color: "#ffffff"
                                    border.color: "#d0d0d0"
                                    radius: 2
                                }
                            }
                            
                            Button {
                                text: "Создать профили"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                enabled: manualProfileNames.text.trim() !== "" && !isCreating
                                
                                background: Rectangle {
                                    color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                    border.color: "#d0d0d0"
                                    radius: 2
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    horizontalAlignment: Text.AlignHCenter
                                    color: parent.enabled ? "#000000" : "#999999"
                                }
                                
                                onClicked: {
                                    isCreating = true
                                    profileManager.createProfilesManually(manualProfileNames.text)
                                }
                            }
                        }
                    }
                    
                    // Панель автоматического создания профилей
                    Rectangle {
                        id: autoCreationPanel
                        Layout.fillWidth: true
                        Layout.preferredHeight: 300
                        color: "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 4
                        visible: false
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 15
                            
                            Text {
                                text: "Укажите количество профилей"
                                font.pixelSize: 14
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            
                            SpinBox {
                                id: profileCount
                                Layout.fillWidth: true
                                from: 1
                                to: 100
                                value: 5
                                editable: true
                            }
                            
                            Text {
                                text: "Префикс имени профиля (необязательно)"
                                font.pixelSize: 14
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            
                            TextField {
                                id: profilePrefix
                                Layout.fillWidth: true
                                placeholderText: "Например: profile_"
                                
                                background: Rectangle {
                                    color: "#ffffff"
                                    border.color: "#d0d0d0"
                                    radius: 2
                                }
                            }
                            
                            Item {
                                Layout.fillHeight: true
                            }
                            
                            Button {
                                text: "Создать профили"
                                Layout.fillWidth: true
                                Layout.preferredHeight: 40
                                enabled: !isCreating
                                
                                background: Rectangle {
                                    color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                                    border.color: "#d0d0d0"
                                    radius: 2
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    horizontalAlignment: Text.AlignHCenter
                                    color: parent.enabled ? "#000000" : "#999999"
                                }
                                
                                onClicked: {
                                    isCreating = true
                                    profileManager.createProfilesAutomatically(profileCount.value, profilePrefix.text)
                                }
                            }
                        }
                    }
                    
                    // Сообщение о статусе создания профилей
                    Rectangle {
                        id: creationStatusMessage
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        property bool success: creationSuccess
                        property string message: creationStatus
                        
                        color: success ? "#e6f7e6" : "#ffebee"  // Зеленый для успеха, красный для ошибки
                        border.color: success ? "#c3e6c3" : "#ffcdd2"
                        radius: 4
                        visible: false
                        
                        Text {
                            anchors.centerIn: parent
                            text: creationStatusMessage.message
                            color: creationStatusMessage.success ? "#2e7d32" : "#c62828"  // Темно-зеленый или темно-красный для текста
                            font.pixelSize: 14
                            width: parent.width - 20
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                        }
                        
                        // Таймер для скрытия сообщения
                        Timer {
                            id: creationStatusTimer
                            interval: 3000  // 3 секунды
                            onTriggered: creationStatusMessage.visible = false
                        }
                    }
                    
                    // Растягивающийся элемент для заполнения пространства
                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
        }
        
        // Кнопка закрытия
        Button {
            text: "🏠 Закрыть окно"
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            flat: true
            enabled: !isProcessing && !isCreating
            
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
    
    // Диалог переименования списка
    Dialog {
        id: renameDialog
        title: "Переименовать список"
        modal: true
        anchors.centerIn: parent
        width: 400
        
        property string listId: ""
        property string listName: ""
        
        contentItem: ColumnLayout {
            spacing: 10
            
            Text {
                text: "Введите новое название для списка:"
                Layout.fillWidth: true
            }
            
            TextField {
                id: newNameField
                Layout.fillWidth: true
                text: renameDialog.listName
                
                background: Rectangle {
                    color: "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Button {
                    text: "Отмена"
                    Layout.fillWidth: true
                    
                    background: Rectangle {
                        color: parent.hovered ? "#e0e0e0" : "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 3
                    }
                    
                    onClicked: renameDialog.close()
                }
                
                Button {
                    text: "Сохранить"
                    Layout.fillWidth: true
                    enabled: newNameField.text.trim() !== ""
                    
                    background: Rectangle {
                        color: parent.enabled ? (parent.hovered ? "#e0e0e0" : "#ffffff") : "#f5f5f5"
                        border.color: "#d0d0d0"
                        radius: 3
                    }
                    
                    onClicked: {
                        isProcessing = true
                        profileManager.renameProfileList(renameDialog.listId, newNameField.text.trim())
                        renameDialog.close()
                    }
                }
            }
        }
    }
    
    // Диалог удаления списка
    Dialog {
        id: deleteDialog
        title: "Удалить список"
        modal: true
        anchors.centerIn: parent
        width: 400
        
        property string listId: ""
        property string listName: ""
        
        contentItem: ColumnLayout {
            spacing: 10
            
            Text {
                text: "Вы уверены, что хотите удалить список \"" + deleteDialog.listName + "\"?"
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            
            Text {
                text: "Профили не будут удалены, только их группировка в список."
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#666666"
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Button {
                    text: "Отмена"
                    Layout.fillWidth: true
                    
                    background: Rectangle {
                        color: parent.hovered ? "#e0e0e0" : "#ffffff"
                        border.color: "#d0d0d0"
                        radius: 3
                    }
                    
                    onClicked: deleteDialog.close()
                }
                
                Button {
                    text: "Удалить"
                    Layout.fillWidth: true
                    
                    background: Rectangle {
                        color: parent.hovered ? "#ffebee" : "#ffffff"
                        border.color: "#ffcdd2"
                        radius: 3
                    }
                    
                    contentItem: Text {
                        text: parent.text
                        horizontalAlignment: Text.AlignHCenter
                        color: "#c62828"
                    }
                    
                    onClicked: {
                        isProcessing = true
                        profileManager.deleteProfileList(deleteDialog.listId)
                        deleteDialog.close()
                    }
                }
            }
        }
    }
} 
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    objectName: "profileLauncher"
    title: "Запуск профилей - Chrome Profile Manager"
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
    
    // Текущий выбранный список
    property string currentListId: ""
    property string currentListName: ""
    
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
    }
    
    // Основной макет
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10
        
        // Заголовок
        Text {
            text: "Запуск профилей Chrome"
            font.pixelSize: 20
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }
        
        // Основной контент
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15
            
            // Левая панель - списки профилей
            Rectangle {
                Layout.preferredWidth: 250
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
                            // Сбрасываем текущий список в ProfileManager
                            profileManager.resetCurrentList()
                        }
                    }
                    
                    // Поле поиска по спискам
                    TextField {
                        id: listSearchField
                        Layout.fillWidth: true
                        placeholderText: "Поиск списков..."
                        
                        background: Rectangle {
                            color: "#ffffff"
                            border.color: "#d0d0d0"
                            radius: 2
                        }
                        
                        onTextChanged: {
                            profileManager.searchProfileLists(text)
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
                            }
                        }
                    }
                }
            }
            
            // Правая панель - профили
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
                        text: currentListName ? "Профили в списке: " + currentListName : "Все профили"
                        font.pixelSize: 16
                        font.bold: true
                        Layout.fillWidth: true
                    }
                    
                    // Поиск профилей
                    TextField {
                        id: profileSearchField
                        Layout.fillWidth: true
                        placeholderText: "Поиск профилей..."
                        
                        background: Rectangle {
                            color: "#ffffff"
                            border.color: "#d0d0d0"
                            radius: 2
                        }
                        
                        onTextChanged: {
                            if (currentListId === "") {
                                profileManager.searchProfilesByName(text)
                            } else {
                                // Если выбран список, то поиск только внутри этого списка
                                // Пока не реализовано, нужно добавить метод в ProfileManager
                            }
                        }
                    }
                    
                    // Список профилей с чекбоксами
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
                    
                    // Кнопки управления
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        Button {
                            text: "Запустить выбранные профили"
                            Layout.fillWidth: true
                            enabled: profileManager.hasSelectedProfiles && !isProcessing
                            
                            background: Rectangle {
                                color: parent.enabled ? (parent.hovered ? "#e0f2f1" : "#ffffff") : "#f5f5f5"
                                border.color: "#26a69a"
                                radius: 3
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                horizontalAlignment: Text.AlignHCenter
                                color: parent.enabled ? "#00796b" : "#999999"
                            }
                            
                            onClicked: {
                                isProcessing = true
                                profileManager.launchSelectedProfiles()
                                isProcessing = false
                            }
                        }
                        
                        Button {
                            text: "Запустить все профили из списка"
                            Layout.fillWidth: true
                            enabled: currentListId !== "" && !isProcessing
                            
                            background: Rectangle {
                                color: parent.enabled ? (parent.hovered ? "#e0f2f1" : "#ffffff") : "#f5f5f5"
                                border.color: "#26a69a"
                                radius: 3
                            }
                            
                            contentItem: Text {
                                text: parent.text
                                horizontalAlignment: Text.AlignHCenter
                                color: parent.enabled ? "#00796b" : "#999999"
                            }
                            
                            onClicked: {
                                isProcessing = true
                                profileManager.launchProfilesFromList(currentListId)
                                isProcessing = false
                            }
                        }
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
        
        // Сообщение о статусе
        Rectangle {
            id: statusMessage
            Layout.fillWidth: true
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
} 
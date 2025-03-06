import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()
    
    // Состояние создания профилей
    property bool isCreating: false
    property string creationStatus: ""
    property bool creationSuccess: false
    
    // Обработка сигнала о статусе создания профилей
    Connections {
        target: profileManager
        function onProfileCreationStatusChanged(success, message) {
            isCreating = false
            creationStatus = message
            creationSuccess = success
            statusMessage.visible = true
            statusTimer.restart()
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 15

        // Заголовок
        Text {
            text: "Создание профилей"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Выберите способ создания профилей"
            font.pixelSize: 14
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Layout.bottomMargin: 5
        }

        // Кнопки выбора способа создания
        Button {
            text: "📝 задать вручную"
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
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
                color: parent.enabled ? "#000000" : "#999999"
            }
            
            onClicked: {
                manualCreationPanel.visible = true
                autoCreationPanel.visible = false
            }
        }
        
        Button {
            text: "🤖 задать автоматически"
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
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
                color: parent.enabled ? "#000000" : "#999999"
            }
            
            onClicked: {
                manualCreationPanel.visible = false
                autoCreationPanel.visible = true
            }
        }
        
        // Панель ручного создания профилей
        Rectangle {
            id: manualCreationPanel
            Layout.fillWidth: true
            Layout.preferredHeight: 200
            color: "#ffffff"
            border.color: "#d0d0d0"
            radius: 4
            visible: false
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                
                Text {
                    text: "Введите имена профилей (через запятую)"
                    font.pixelSize: 14
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
            Layout.preferredHeight: 200
            color: "#ffffff"
            border.color: "#d0d0d0"
            radius: 4
            visible: false
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10
                
                Text {
                    text: "Укажите количество профилей"
                    font.pixelSize: 14
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
        
        // Сообщение о статусе
        Rectangle {
            id: statusMessage
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            Layout.topMargin: 10
            property bool success: creationSuccess
            property string message: creationStatus
            
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
        
        // Растягивающийся элемент для заполнения пространства
        Item {
            Layout.fillHeight: true
        }
        
        // Кнопка "Назад"
        Button {
            text: "🏠 назад в меню"
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            flat: true
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
            
            onClicked: root.backClicked()
        }
    }
} 
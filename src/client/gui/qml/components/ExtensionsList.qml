import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()
    
    // Модель для списка расширений
    property var extensionsModel: []
    
    // Состояние операций с расширениями
    property bool isProcessing: false
    property string operationStatus: ""
    property bool operationSuccess: false
    
    // Выбранные расширения для массового удаления
    property var selectedExtensions: []
    
    // Обработка сигнала о статусе операций с расширениями
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
            extensionsModel = extensions
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 15

        // Заголовок
        Text {
            text: "Установленные расширения"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Список всех установленных расширений"
            font.pixelSize: 14
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Layout.bottomMargin: 5
        }
        
        // Кнопки для массового удаления
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            visible: selectedExtensions.length > 0
            
            Text {
                text: "Выбрано: " + selectedExtensions.length
                font.pixelSize: 14
                Layout.fillWidth: true
            }
            
            Button {
                text: "Удалить выбранные из всех профилей"
                Layout.fillWidth: true
                enabled: !isProcessing
                
                onClicked: {
                    isProcessing = true
                    profileManager.removeMultipleExtensionsFromAllProfiles(selectedExtensions)
                    selectedExtensions = [] // Очищаем выбранные расширения
                }
            }
            
            Button {
                text: "Удалить из выбранных профилей"
                Layout.fillWidth: true
                enabled: !isProcessing
                
                onClicked: {
                    profileSelectionDialog.extensionsToRemove = selectedExtensions
                    profileSelectionDialog.open()
                }
            }
        }
        
        // Список расширений
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            
            ListView {
                id: extensionsListView
                width: parent.width
                model: extensionsModel
                
                delegate: Rectangle {
                    width: extensionsListView.width
                    height: extensionLayout.height + 20
                    color: index % 2 === 0 ? "#ffffff" : "#f5f5f5"
                    
                    ColumnLayout {
                        id: extensionLayout
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.margins: 10
                        spacing: 5
                        
                        RowLayout {
                            Layout.fillWidth: true
                            
                            CheckBox {
                                id: extensionCheckbox
                                checked: selectedExtensions.includes(modelData.id)
                                
                                onCheckedChanged: {
                                    if (checked) {
                                        // Добавляем расширение в список выбранных
                                        if (!selectedExtensions.includes(modelData.id)) {
                                            selectedExtensions.push(modelData.id)
                                        }
                                    } else {
                                        // Удаляем расширение из списка выбранных
                                        var index = selectedExtensions.indexOf(modelData.id)
                                        if (index !== -1) {
                                            selectedExtensions.splice(index, 1)
                                        }
                                    }
                                }
                            }
                            
                            // Иконка расширения
                            Image {
                                source: modelData.iconUrl ? modelData.iconUrl : ""
                                width: 32
                                height: 32
                                fillMode: Image.PreserveAspectFit
                                visible: modelData.iconUrl !== ""
                                
                                // Заглушка, если иконка не загрузилась
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#e0e0e0"
                                    radius: 4
                                    visible: parent.status !== Image.Ready && modelData.iconUrl !== ""
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: "?"
                                        font.pixelSize: 16
                                    }
                                }
                            }
                            
                            // Заглушка, если иконки нет
                            Rectangle {
                                width: 32
                                height: 32
                                color: "#e0e0e0"
                                radius: 4
                                visible: modelData.iconUrl === ""
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "E"
                                    font.pixelSize: 16
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
                                    color: "#888888"
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                
                                // Список профилей, в которых установлено расширение
                                Text {
                                    text: "Установлено в: " + (modelData.profiles ? modelData.profiles.join(", ") : "")
                                    font.pixelSize: 10
                                    color: "#888888"
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                    visible: modelData.profiles && modelData.profiles.length > 0
                                }
                            }
                        }
                        
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: 5
                            
                            Button {
                                text: "Удалить из всех профилей"
                                Layout.fillWidth: true
                                enabled: !isProcessing
                                
                                onClicked: {
                                    isProcessing = true
                                    profileManager.removeExtensionFromAllProfiles(modelData.id)
                                }
                            }
                            
                            Button {
                                text: "Удалить из выбранных"
                                Layout.fillWidth: true
                                enabled: !isProcessing
                                
                                onClicked: {
                                    profileSelectionDialog.extensionToRemove = modelData.id
                                    profileSelectionDialog.open()
                                }
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
        
        // Диалог выбора профилей
        Dialog {
            id: profileSelectionDialog
            title: "Выберите профили"
            width: parent.width * 0.9
            height: parent.height * 0.7
            anchors.centerIn: parent
            modal: true
            
            property string extensionToRemove: ""
            property var extensionsToRemove: []
            
            contentItem: Rectangle {
                color: "#f0f0f0"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    
                    ListView {
                        id: profileListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        model: profileManager.profilesList
                        
                        delegate: CheckBox {
                            width: profileListView.width
                            text: modelData
                            checked: profileManager.isProfileSelected(modelData)
                            onCheckedChanged: profileManager.toggleProfileSelection(modelData, checked)
                        }
                    }
                    
                    RowLayout {
                        Layout.fillWidth: true
                        
                        Button {
                            text: "Выбрать все"
                            Layout.fillWidth: true
                            onClicked: profileManager.selectAllProfiles()
                        }
                        
                        Button {
                            text: "Снять выбор"
                            Layout.fillWidth: true
                            onClicked: profileManager.deselectAllProfiles()
                        }
                    }
                    
                    Button {
                        text: "Удалить расширение"
                        Layout.fillWidth: true
                        enabled: profileManager.hasSelectedProfiles
                        visible: profileSelectionDialog.extensionToRemove !== ""
                        
                        onClicked: {
                            isProcessing = true
                            profileManager.removeExtensionFromSelectedProfiles(profileSelectionDialog.extensionToRemove)
                            profileSelectionDialog.close()
                        }
                    }
                    
                    Button {
                        text: "Удалить выбранные расширения"
                        Layout.fillWidth: true
                        enabled: profileManager.hasSelectedProfiles && profileSelectionDialog.extensionsToRemove.length > 0
                        visible: profileSelectionDialog.extensionsToRemove.length > 0
                        
                        onClicked: {
                            isProcessing = true
                            profileManager.removeMultipleExtensionsFromSelectedProfiles(profileSelectionDialog.extensionsToRemove)
                            selectedExtensions = [] // Очищаем выбранные расширения
                            profileSelectionDialog.close()
                        }
                    }
                    
                    Button {
                        text: "Отмена"
                        Layout.fillWidth: true
                        onClicked: profileSelectionDialog.close()
                    }
                }
            }
            
            onOpened: {
                // Сбрасываем свойства при открытии диалога
                if (extensionsToRemove.length > 0) {
                    extensionToRemove = ""
                } else if (extensionToRemove !== "") {
                    extensionsToRemove = []
                }
            }
        }
        
        // Кнопки управления
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            Button {
                text: "Обновить список"
                Layout.fillWidth: true
                enabled: !isProcessing
                
                onClicked: {
                    isProcessing = true
                    selectedExtensions = [] // Очищаем выбранные расширения
                    profileManager.getInstalledExtensionsList()
                }
            }
            
            Button {
                text: "Выбрать все"
                Layout.fillWidth: true
                enabled: !isProcessing && extensionsModel.length > 0
                
                onClicked: {
                    // Выбираем все расширения
                    selectedExtensions = []
                    for (var i = 0; i < extensionsModel.length; i++) {
                        selectedExtensions.push(extensionsModel[i].id)
                    }
                }
            }
            
            Button {
                text: "Снять выбор"
                Layout.fillWidth: true
                enabled: !isProcessing && selectedExtensions.length > 0
                
                onClicked: {
                    // Снимаем выбор со всех расширений
                    selectedExtensions = []
                }
            }
            
            Button {
                text: "🏠 Назад"
                Layout.fillWidth: true
                enabled: !isProcessing
                
                onClicked: root.backClicked()
            }
        }
    }
} 
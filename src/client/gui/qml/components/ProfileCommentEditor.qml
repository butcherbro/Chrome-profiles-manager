import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()

    property string comment: ""
    
    // Функция для обновления текста комментария при выборе профиля
    function updateCommentField() {
        // Если выбран только один профиль, показываем его комментарий
        var selectedProfiles = profileManager.profilesList.filter(function(profile) {
            return profileManager.isProfileSelected(profile);
        });
        
        if (selectedProfiles.length === 1) {
            root.comment = profileManager.getProfileComment(selectedProfiles[0]);
        } else if (selectedProfiles.length > 1) {
            // Если выбрано несколько профилей, проверяем, одинаковые ли у них комментарии
            var firstComment = profileManager.getProfileComment(selectedProfiles[0]);
            var allSame = true;
            
            for (var i = 1; i < selectedProfiles.length; i++) {
                if (profileManager.getProfileComment(selectedProfiles[i]) !== firstComment) {
                    allSame = false;
                    break;
                }
            }
            
            if (allSame) {
                root.comment = firstComment;
            } else {
                root.comment = ""; // Разные комментарии, очищаем поле
            }
        } else {
            root.comment = ""; // Нет выбранных профилей
        }
    }
    
    // Обновляем комментарий при изменении выбранных профилей
    Connections {
        target: profileManager
        function onSelectedProfilesChanged() {
            updateCommentField();
        }
        
        // Обработка сигнала о статусе сохранения
        function onCommentSaveStatusChanged(success, message) {
            saveMessage.success = success;
            saveMessage.message = message;
            saveMessage.visible = true;
            saveMessageTimer.restart();
        }
    }
    
    // Обновляем комментарий при загрузке компонента
    Component.onCompleted: {
        updateCommentField();
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 15

        // Заголовок
        Text {
            text: "Обновление комментариев"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Выберите профили и введите комментарий"
            font.pixelSize: 14
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Layout.bottomMargin: 5
        }

        // Список профилей
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: profileList
                anchors.fill: parent
                model: profileManager.profilesList
                spacing: 8

                delegate: Item {
                    width: parent.width
                    height: 50
                    
                    RowLayout {
                        anchors.fill: parent
                        spacing: 5
                        
                        CheckBox {
                            id: checkBox
                            text: ""
                            Layout.preferredWidth: 30
                            checked: profileManager.isProfileSelected(modelData)
                            
                            // Обработчик изменения состояния
                            onCheckedChanged: {
                                profileManager.toggleProfileSelection(modelData, checked)
                            }
                            
                            // Компонент для принудительного обновления состояния
                            Connections {
                                target: profileManager
                                function onSelectedProfilesChanged() {
                                    checkBox.checked = profileManager.isProfileSelected(modelData)
                                }
                            }
                        }
                        
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            
                            Text {
                                text: modelData
                                font.pixelSize: 14
                                font.bold: true
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            
                            Text {
                                text: profileManager.getProfileComment(modelData)
                                font.pixelSize: 12
                                color: "#666666"
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                                visible: text !== ""
                            }
                        }
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
        }

        // Поле ввода комментария
        TextArea {
            id: commentField
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            placeholderText: "Введите комментарий для выбранных профилей"
            text: root.comment
            onTextChanged: {
                root.comment = text
            }
            
            background: Rectangle {
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 2
            }
        }

        // Кнопки управления
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                text: "Выбрать все"
                Layout.fillWidth: true
                flat: true
                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }
                onClicked: {
                    profileManager.selectAllProfiles()
                }
            }

            Button {
                text: "Снять выбор"
                Layout.fillWidth: true
                flat: true
                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }
                onClicked: {
                    profileManager.deselectAllProfiles()
                }
            }
        }

        // Кнопки действий
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Layout.topMargin: 10

            Button {
                text: "Сохранить"
                Layout.fillWidth: true
                flat: true
                enabled: profileManager.hasSelectedProfiles && commentField.text.trim() !== ""
                
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
                    profileManager.updateProfileComments(commentField.text)
                    // Не показываем сообщение здесь, оно будет показано по сигналу commentSaveStatusChanged
                }
            }

            Button {
                text: "Назад"
                Layout.fillWidth: true
                flat: true
                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }
                onClicked: root.backClicked()
            }
        }
        
        // Сообщение об успешном сохранении
        Rectangle {
            id: saveMessage
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            Layout.topMargin: 10
            property bool success: true
            property string message: "Комментарии успешно сохранены"
            
            color: success ? "#e6f7e6" : "#ffebee"  // Зеленый для успеха, красный для ошибки
            border.color: success ? "#c3e6c3" : "#ffcdd2"
            radius: 4
            visible: false
            
            Text {
                anchors.centerIn: parent
                text: saveMessage.message
                color: saveMessage.success ? "#2e7d32" : "#c62828"  // Темно-зеленый или темно-красный для текста
                font.pixelSize: 14
                width: parent.width - 20
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            
            // Таймер для скрытия сообщения
            Timer {
                id: saveMessageTimer
                interval: 3000  // 3 секунды
                onTriggered: saveMessage.visible = false
            }
        }
    }
} 
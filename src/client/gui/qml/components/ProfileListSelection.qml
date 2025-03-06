import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()

    // Состояние для принудительного обновления чекбоксов
    property bool selectAllState: false
    
    Connections {
        target: profileManager
        function onSelectedProfilesChanged() {
            profileList.forceLayout()
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Заголовок
        Text {
            text: "Выберите профили"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
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
                    selectAllState = !selectAllState // Переключаем состояние для обновления
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
                    selectAllState = !selectAllState // Переключаем состояние для обновления
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
                text: "Запустить"
                Layout.fillWidth: true
                flat: true
                background: Rectangle {
                    color: parent.hovered ? "#e0e0e0" : "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
                }
                onClicked: {
                    profileManager.launchSelectedProfiles()
                    root.backClicked()
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
    }
} 
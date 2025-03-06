import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()

    property string searchText: ""
    property var filteredProfiles: []
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Заголовок
        Text {
            text: "Поиск по комментарию"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Поле поиска
        TextField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: "Введите текст для поиска"
            text: root.searchText
            onTextChanged: {
                root.searchText = text
                profileManager.searchProfilesByComment(text)
            }
            
            background: Rectangle {
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 2
            }
        }

        // Список найденных профилей
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: profileList
                anchors.fill: parent
                model: profileManager.filteredProfilesList
                spacing: 8

                delegate: CheckBox {
                    id: checkBox
                    width: parent.width
                    height: 40
                    
                    contentItem: ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 24
                        spacing: 2

                        Text {
                            text: modelData.name
                            font.bold: true
                        }
                        
                        Text {
                            text: modelData.comment
                            color: "#666666"
                            font.pixelSize: 12
                        }
                    }

                    checked: profileManager.isProfileSelected(modelData.name)
                    onCheckedChanged: profileManager.toggleProfileSelection(modelData.name, checked)
                }
            }
        }

        // Кнопки действий
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Layout.topMargin: 20

            Button {
                text: "Запустить"
                Layout.fillWidth: true
                flat: true
                enabled: profileManager.hasSelectedProfiles
                
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
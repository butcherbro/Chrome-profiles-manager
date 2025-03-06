import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()

    property string profileNames: ""
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Заголовок
        Text {
            text: "Введите имена профилей"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Введите имена профилей через запятую"
            font.pixelSize: 14
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Layout.bottomMargin: 10
        }

        // Поле ввода
        TextArea {
            id: namesField
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            placeholderText: "Например: profile1, profile2, profile3"
            text: root.profileNames
            onTextChanged: {
                root.profileNames = text
            }
            
            background: Rectangle {
                color: "#ffffff"
                border.color: "#d0d0d0"
                radius: 2
            }
        }

        // Список введенных профилей
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: parsedProfilesList.count > 0

            ListView {
                id: parsedProfilesList
                anchors.fill: parent
                model: namesField.text.split(',').filter(name => name.trim().length > 0).map(name => name.trim())
                spacing: 8

                delegate: Rectangle {
                    width: parent.width
                    height: 40
                    color: "#ffffff"
                    radius: 2
                    border.color: "#d0d0d0"

                    Text {
                        anchors.fill: parent
                        anchors.margins: 10
                        text: modelData
                        verticalAlignment: Text.AlignVCenter
                    }
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
                enabled: parsedProfilesList.count > 0
                
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
                    var profileNames = namesField.text.split(',').filter(name => name.trim().length > 0).map(name => name.trim())
                    profileManager.launchProfilesByNames(profileNames)
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
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()

    property string inputText: ""
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Заголовок
        Text {
            text: "Введите названия профилей"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Введите названия профилей через запятую"
            font.pixelSize: 14
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 20
            color: "#666666"
        }

        // Поле ввода
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 100
            clip: true

            TextArea {
                id: namesInput
                width: parent.width
                wrapMode: TextArea.Wrap
                placeholderText: "Например: profile1, profile2, profile3"
                text: root.inputText
                onTextChanged: root.inputText = text
                
                background: Rectangle {
                    color: "#ffffff"
                    border.color: "#d0d0d0"
                    radius: 2
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
                enabled: namesInput.text.trim() !== ""
                
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
                    let profileNames = namesInput.text.split(',')
                        .map(name => name.trim())
                        .filter(name => name !== "")
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